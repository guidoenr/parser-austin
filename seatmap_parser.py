import sys
import xml.etree.ElementTree as ET
import json

xml_doc = str(sys.argv[1])
tree = ET.parse(xml_doc)
root = tree.getroot()

#This section is going to make some assumptions in regards to scalability. The XML documents provided either come from IATA or #Opentravel, and the biggest assumption in regards to this is that IATA follows one format consistently, and Opentravel follows the #other. 
#Here is where we'll find out which file is presented and how it will be handled.
Rows = []
class FlightObject:
    def __init__ (self, departure_date_time, departure_loc, arrival_loc, equipment_type, row):
        self.departure_date_time = departure_date_time
        self.departure_loc = departure_loc
        self.arrival_loc = arrival_loc
        self.equipment_type = equipment_type
        self.row = row

class RowObject:
    def __init__ (self, class_type, row_numbers, seat):
        self.class_type = class_type
        self.row_numbers = row_numbers
        self.seat = seat

class SeatObject:
    def __init__ (self, seat_id, avail_status, feature, price):
        self.seat_id = seat_id
        self.avail_status = avail_status
        self.feature = feature
        self.price = price

#This section is for OpenTravel xml processing. In the event that there's a bit that IATA will use, these will be recycled, but
#IATA and OpenTravel apparently didn't get each other's memos on how to build their respective websites.

def strip_url_from_tag(child_info):
    entire_tag = str(child_info)
    url_information, unused_portion = entire_tag.split("}")
    url_information += "}"
    return url_information

def get_information(used_dict, info_needed):
    info = str(used_dict.get(info_needed))
    if info_needed == 'Amount' or info_needed == 'DecimalPlaces':
        info = make_float(info)
    return info

def flight_departure(url_information):
    for flight_departure_date_time in root.iter('{}FlightSegmentInfo'.format(url_information)):
        flight_departure_date_time = get_information(flight_departure_date_time.attrib,'DepartureDateTime')
        return flight_departure_date_time

def departure_loc(url_information):
    for flight_departure_loc in root.iter('{}DepartureAirport'.format(url_information)):
        flight_departure_loc = get_information(flight_departure_loc.attrib, 'LocationCode')
        return flight_departure_loc

def arrival_loc(url_information):
    for flight_arrival_loc in root.iter('{}ArrivalAirport'.format(url_information)):
        flight_arrival_loc = get_information(flight_arrival_loc.attrib, 'LocationCode')
        return flight_arrival_loc

def equipment_type(url_information):
    for flight_equip_type in root.iter('{}Equipment'.format(url_information)):
        flight_equip_type = get_information(flight_equip_type.attrib, 'AirEquipType')
        return flight_equip_type

def make_float(info_to_convert):
    converted_to_float = float(info_to_convert)
    return converted_to_float

def get_seat_info(seat_dict):
    seat_id = get_information(seat_dict, 'SeatNumber')
    avail_status = get_information(seat_dict, 'AvailableInd')
    if avail_status == 'false':
        avail_status = 'Unavailable'
    else:
        avail_status = 'Available'
    return seat_id, avail_status

def get_fees_info(fees_dict):
    amount = get_information(fees_dict, 'Amount')
    decimal = get_information(fees_dict, 'DecimalPlaces')
    currency = get_information(fees_dict, 'CurrencyCode')
    places = 10 ** (-1 * decimal)
    total = amount * places
    price = '{:,.2f} '.format(total) + currency
    return price

def get_class(row_info_dict):
    class_type = get_information(row_info_dict, 'CabinType')
    row_number = get_information(row_info_dict, 'RowNumber')
    return class_type, row_number

def ota_flight_handling(url_information):
    flight_departure_date_time = flight_departure(url_information)
    flight_departure_loc = departure_loc(url_information)
    flight_arrival_loc = arrival_loc(url_information)
    flight_equip_type = equipment_type(url_information)

    for row_info in root.iter('{}RowInfo'.format(url_information)):
        Seats = []
        price = ""
        for seat_info in row_info.iter('{}SeatInfo'.format(url_information)):
            for seat in seat_info.iter('{}Summary'.format(url_information)):
                seat = seat.attrib
                seat_id, avail_status = get_seat_info(seat)
            for features in seat_info.iter('{}Features'.format(url_information)):
                feature_check = features.text
                if feature_check != "Other_":
                    feature = feature_check
            for service in seat_info.iter('{}Service'.format(url_information)):
                for fees in service.iter('{}Fee'.format(url_information)):
                    fees = fees.attrib
                    price = get_fees_info(fees)
            seat_object = SeatObject(seat_id, avail_status, feature, price)
            seat = seat_object.__dict__
            Seats.append(seat)
        row_info = row_info.attrib
        class_type, row_number = get_class(row_info)
        row_object = RowObject(class_type, row_number, Seats)
        row = row_object.__dict__
        Rows.append(row)
    flight_obect = FlightObject(flight_departure_date_time, flight_departure_loc, flight_arrival_loc, flight_equip_type, Rows)
    return flight_obect

#The following section is to handle IATA's flight information XML file. Again, any functions not found therein are likely in
#the section above (OpenTravel's), but it's highly unlikely much code will be shared other than classes.
#def get_price_info(url_information, offer_id):
#    for child in root:
#        for alacarte in child.iter('{}ALaCarteOffer'.format(url_information)):
#            for alacarte_offer in alacarte.iter('{}ALaCarteOfferItem'.format(url_information)):
#                print(alacarte_offer.tag, alacarte_offer.attrib)
#                offer_item_id = get_information(alacarte_offer.attrib, 'OfferItemID')
#                print(offer_item_id)
#                #this should be fetching the seat and returning things specific to that seat by order item.. I think. The offer
#                #should be checked against a passed variable. Current value is specifically for local testing for now.
#                if offer_item_id == 'OFIa20ae42f-6417-11eb-b326-15132ca0c3354':
#                    for eligibility in alacarte_offer.iter('{}Eligibility'.format(url_information)):
#                        print(eligibility.attrib)
#                        print(eligibility[0].text)
#                    for unit_price_detail in alacarte_offer.iter('{}UnitPriceDetail'.format(url_information)):
#                        for total_amount in unit_price_detail.iter('{}TotalAmount'.format(url_information)):
#                            for simple_currency_price in total_amount.iter('{}SimpleCurrencyPrice'.format(url_information)):
#                                print(simple_currency_price.attrib, simple_currency_price.text)
def check_row(url_information):
    layout_starting_row = []
    for child in root:
        for cabin in child.iter('{}Cabin'.format(url_information)):
            for cabin_layout in cabin.iter('{}CabinLayout'.format(url_information)):
                for rows in cabin_layout.iter('{}Rows'.format(url_information)):
                    first = rows.find('{}First'.format(url_information))
                    last = rows.find('{}Last'.format(url_information))
                    layout_starting_row.append(first.text)
                    layout_ending_row = last.text                     
    return layout_starting_row, layout_ending_row

def layout_handler(url_information):
    first_row, last_row = check_row(url_information)
    counter = 0
    print(first_row)
    for child in root:
        for cabin in child.iter('{}Cabin'.format(url_information)):
            print(cabin.tag, cabin.attrib)
            for cabin_layout in cabin.iter('{}CabinLayout'.format(url_information)):
                if len(first_row) - 1 > counter:
                    print("First Row: ", first_row[counter], "- Last Row: ", str(int(first_row[counter+1]) - 1))
                else:
                    print("First Row: ", first_row[counter], "- Last Row: ", last_row)
                for columns in cabin_layout.iter('{}Columns'.format(url_information)):
                    print(columns.attrib, columns.text)
                counter += 1


def iata_flight_handling(url_information):
    layout_handler(url_information)        
                
    print('No programming yet to handle {}. Please try again later'.format(url_information))

for child in root[0]:
    if 'IATA' in child.tag:
        print("IATA flight information recieved!")
        url_information = strip_url_from_tag(child.tag)
        iata_flight_handling(url_information)
#       No code yet for this type, so I'm just going to leave this line in for later
#         flight = iata_flight_handling(url_information)     
    elif 'OTA' in child.tag:
        print("OpenTravel flight information received!")
        url_information = strip_url_from_tag(child.tag)
        flight = ota_flight_handling(url_information)
    else:
        print("Invalid File Type")


file_name = xml_doc.replace(".xml", "_parsed.json")
#make certain to uncomment this before running final program
#flight_info = flight.__dict__
#with open(file_name, 'w') as outfile:
#    json.dump(flight_info, outfile)
print("Parsing complete! Parsed document found at {}".format(file_name))
#These are helpful links to finish this project:
#https://docs.python.org/3/library/xml.etree.elementtree.html is my ElementTree documentation
#https://anenadic.github.io/2014-11-10-manchester/novice/python/06-cmdline-non-interactive.html is running Python from the command line
#https://www.datacamp.com/community/tutorials/dictionary-python?utm_source=adwords_ppc&utm_campaignid=1565261270&utm_adgroupid=67750485268&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=295208661514&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=9009680&gclid=CjwKCAjw3pWDBhB3EiwAV1c5rCFSPniwB33l4PLFUr1_wJnwssiPVwmvpVDR_mxjAGd7P1dai_dbzRoC03sQAvD_BwE python dictionaries

#print(flight_information)
#This is the basic layout for the command to get the JSON file. For now, we're working on how to get it in the first place. 
#json_file_information = json.dumps(flight_information)
#https://www.w3schools.com/python/python_json.asp describes how to use the built in json function to convert python objects to a json file