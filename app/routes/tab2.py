from flask import Blueprint, render_template, request, jsonify
from collections import defaultdict
from db_connection import DatabaseConnection
import sqlite3
import logging

tab2_bp = Blueprint("tab2_bp", __name__, url_prefix="/tab2")
logging.basicConfig(level=logging.DEBUG)

# Hardcoded mappings from seed data
CATEGORY_MAP = {
    4052: 'Tent Tops', 4054: 'Tent Tops', 4203: 'Tent Tops', 4204: 'Tent Tops', 4213: 'Tent Tops',
    4214: 'Tent Tops', 4292: 'Tent Tops', 4807: 'Tent Tops', 4808: 'Tent Tops', 60526: 'Tent Tops',
    60528: 'Tent Tops', 62706: 'Tent Tops', 62707: 'Tent Tops', 62708: 'Tent Tops', 62709: 'Tent Tops',
    62711: 'Tent Tops', 62714: 'Tent Tops', 62715: 'Tent Tops', 62719: 'Tent Tops', 62723: 'Tent Tops',
    62727: 'Tent Tops', 62731: 'Tent Tops', 62735: 'Tent Tops', 62737: 'Tent Tops', 62745: 'Tent Tops',
    62749: 'Tent Tops', 62750: 'Tent Tops', 62753: 'Tent Tops', 62755: 'Tent Tops', 62757: 'Tent Tops',
    62761: 'Tent Tops', 62762: 'Tent Tops', 62763: 'Tent Tops', 62769: 'Tent Tops', 62770: 'Tent Tops',
    62773: 'Tent Tops', 62781: 'Tent Tops', 62782: 'Tent Tops', 62805: 'Tent Tops', 62806: 'Tent Tops',
    62807: 'Tent Tops', 62808: 'Tent Tops', 62809: 'Tent Tops', 62810: 'Tent Tops', 62853: 'Tent Tops',
    62857: 'Tent Tops', 62858: 'Tent Tops', 62859: 'Tent Tops', 62861: 'Tent Tops', 62862: 'Tent Tops',
    62864: 'Tent Tops', 62865: 'Tent Tops', 62867: 'Tent Tops', 62868: 'Tent Tops', 62871: 'Tent Tops',
    62872: 'Tent Tops', 62875: 'Tent Tops', 62876: 'Tent Tops', 62883: 'Tent Tops', 62887: 'Tent Tops',
    62891: 'Tent Tops', 62894: 'Tent Tops', 62895: 'Tent Tops', 62896: 'Tent Tops', 62797: 'Tent Tops',
    62798: 'Tent Tops', 62900: 'Tent Tops', 62901: 'Tent Tops', 62902: 'Tent Tops', 62904: 'Tent Tops',
    62905: 'Tent Tops', 62906: 'Tent Tops', 65035: 'Tent Tops', 65036: 'Tent Tops', 65037: 'Tent Tops',
    65039: 'Tent Tops', 65367: 'Tent Tops', 65119: 'Tent Tops', 65446: 'Tent Tops', 65449: 'Tent Tops',
    65450: 'Tent Tops', 65467: 'Tent Tops', 65468: 'Tent Tops', 65469: 'Tent Tops', 66324: 'Tent Tops',
    66325: 'Tent Tops', 66326: 'Tent Tops', 67657: 'Tent Tops', 65129: 'Tent Tops', 66363: 'Tent Tops',
    72252: 'Tent Tops', 72253: 'Tent Tops', 72392: 'Tent Tops', 72401: 'Tent Tops', 72402: 'Tent Tops',
    72403: 'Tent Tops', 72404: 'Tent Tops', 72405: 'Tent Tops', 72406: 'Tent Tops', 72407: 'Tent Tops',
    72408: 'Tent Tops', 72409: 'Tent Tops', 72410: 'Tent Tops', 72411: 'Tent Tops', 72412: 'Tent Tops',
    62668: 'Tent Tops', 62669: 'Tent Tops', 62681: 'Tent Tops', 62682: 'Tent Tops', 62683: 'Tent Tops',
    62684: 'Tent Tops', 62686: 'Tent Tops', 62803: 'Tent Tops', 63851: 'Tent Tops', 63852: 'Tent Tops',
    60533: 'AV Equipment', 60537: 'AV Equipment', 60731: 'AV Equipment', 60735: 'AV Equipment',
    61543: 'AV Equipment', 61545: 'AV Equipment', 61548: 'AV Equipment', 61566: 'AV Equipment',
    61570: 'AV Equipment', 61571: 'AV Equipment', 61572: 'AV Equipment', 61573: 'AV Equipment',
    63343: 'AV Equipment', 63359: 'AV Equipment', 63430: 'AV Equipment', 63131: 'Tables and Chairs',
    63133: 'Tables and Chairs', 65171: 'Tables and Chairs', 65722: 'Tables and Chairs',
    61771: 'Tables and Chairs', 61772: 'Tables and Chairs', 61824: 'Round Linen', 61825: 'Round Linen',
    61826: 'Round Linen', 61882: 'Round Linen', 61883: 'Round Linen', 61827: 'Round Linen',
    61828: 'Round Linen', 61830: 'Round Linen', 61831: 'Round Linen', 61832: 'Round Linen',
    61833: 'Round Linen', 61834: 'Round Linen', 61835: 'Round Linen', 61836: 'Round Linen',
    61837: 'Round Linen', 61838: 'Round Linen', 61839: 'Round Linen', 61840: 'Round Linen',
    61842: 'Round Linen', 61843: 'Round Linen', 61846: 'Round Linen', 61847: 'Round Linen',
    61848: 'Round Linen', 61850: 'Round Linen', 61852: 'Round Linen', 61854: 'Round Linen',
    61856: 'Round Linen', 61858: 'Round Linen', 61859: 'Round Linen', 61862: 'Round Linen',
    61863: 'Round Linen', 61864: 'Round Linen', 61865: 'Round Linen', 61866: 'Round Linen',
    61867: 'Round Linen', 61868: 'Round Linen', 61869: 'Round Linen', 61870: 'Round Linen',
    61871: 'Round Linen', 61872: 'Round Linen', 61873: 'Round Linen', 61874: 'Round Linen',
    61875: 'Round Linen', 61876: 'Round Linen', 61879: 'Round Linen', 61880: 'Round Linen',
    61881: 'Round Linen', 61885: 'Round Linen', 61886: 'Round Linen', 61887: 'Round Linen',
    61888: 'Round Linen', 61889: 'Round Linen', 61890: 'Round Linen', 72595: 'Round Linen',
    61891: 'Round Linen', 61893: 'Round Linen', 61895: 'Round Linen', 61896: 'Round Linen',
    61901: 'Round Linen', 61904: 'Round Linen', 61905: 'Round Linen', 61908: 'Round Linen',
    61910: 'Round Linen', 61912: 'Round Linen', 61914: 'Round Linen', 61916: 'Round Linen',
    61921: 'Round Linen', 61922: 'Round Linen', 61924: 'Round Linen', 61925: 'Round Linen',
    61926: 'Round Linen', 61927: 'Round Linen', 61928: 'Round Linen', 61930: 'Round Linen',
    61931: 'Round Linen', 61933: 'Round Linen', 61934: 'Round Linen', 61936: 'Round Linen',
    61937: 'Round Linen', 61939: 'Round Linen', 61942: 'Round Linen', 61943: 'Round Linen',
    61946: 'Round Linen', 61949: 'Round Linen', 61950: 'Round Linen', 61951: 'Round Linen',
    61953: 'Round Linen', 61955: 'Round Linen', 61957: 'Round Linen', 61958: 'Round Linen',
    61960: 'Round Linen', 61961: 'Round Linen', 61962: 'Round Linen', 61964: 'Round Linen',
    61965: 'Round Linen', 61967: 'Round Linen', 61968: 'Round Linen', 61970: 'Round Linen',
    61971: 'Round Linen', 61972: 'Round Linen', 61973: 'Round Linen', 61974: 'Round Linen',
    61975: 'Round Linen', 61976: 'Round Linen', 61977: 'Round Linen', 61978: 'Round Linen',
    61979: 'Round Linen', 61981: 'Round Linen', 61982: 'Round Linen', 61984: 'Round Linen',
    61985: 'Round Linen', 61986: 'Round Linen', 61989: 'Round Linen', 61992: 'Round Linen',
    61994: 'Round Linen', 61996: 'Round Linen', 61999: 'Round Linen', 62003: 'Round Linen',
    62004: 'Round Linen', 62006: 'Round Linen', 62010: 'Round Linen', 62012: 'Round Linen',
    62014: 'Round Linen', 62021: 'Round Linen', 62022: 'Round Linen', 62024: 'Round Linen',
    62025: 'Round Linen', 62026: 'Round Linen', 62027: 'Round Linen', 62028: 'Round Linen',
    62029: 'Round Linen', 62030: 'Round Linen', 62031: 'Round Linen', 62032: 'Round Linen',
    62033: 'Round Linen', 62034: 'Round Linen', 62035: 'Round Linen', 62037: 'Rectangle Linen',
    62038: 'Rectangle Linen', 62039: 'Rectangle Linen', 62040: 'Rectangle Linen', 62041: 'Rectangle Linen',
    62042: 'Rectangle Linen', 62045: 'Rectangle Linen', 62054: 'Rectangle Linen', 62057: 'Rectangle Linen',
    62065: 'Rectangle Linen', 62067: 'Rectangle Linen', 62077: 'Rectangle Linen', 62081: 'Rectangle Linen',
    62082: 'Rectangle Linen', 62083: 'Rectangle Linen', 62085: 'Rectangle Linen', 62086: 'Rectangle Linen',
    62087: 'Rectangle Linen', 62088: 'Rectangle Linen', 62089: 'Rectangle Linen', 62090: 'Rectangle Linen',
    62091: 'Rectangle Linen', 62092: 'Rectangle Linen', 62093: 'Rectangle Linen', 62094: 'Rectangle Linen',
    62095: 'Rectangle Linen', 62096: 'Rectangle Linen', 62098: 'Rectangle Linen', 62099: 'Rectangle Linen',
    62101: 'Rectangle Linen', 62102: 'Rectangle Linen', 62103: 'Rectangle Linen', 62104: 'Rectangle Linen',
    62106: 'Rectangle Linen', 62107: 'Rectangle Linen', 62111: 'Rectangle Linen', 62112: 'Rectangle Linen',
    62113: 'Rectangle Linen', 62114: 'Rectangle Linen', 62116: 'Rectangle Linen', 62117: 'Rectangle Linen',
    62118: 'Rectangle Linen', 62119: 'Rectangle Linen', 62121: 'Rectangle Linen', 62122: 'Rectangle Linen',
    62126: 'Rectangle Linen', 62129: 'Rectangle Linen', 62130: 'Rectangle Linen', 62131: 'Rectangle Linen',
    62132: 'Rectangle Linen', 62133: 'Rectangle Linen', 62134: 'Rectangle Linen', 62136: 'Rectangle Linen',
    62137: 'Rectangle Linen', 62138: 'Rectangle Linen', 62139: 'Rectangle Linen', 62140: 'Rectangle Linen',
    62141: 'Rectangle Linen', 62142: 'Rectangle Linen', 62187: 'Rectangle Linen', 62188: 'Rectangle Linen',
    62189: 'Rectangle Linen', 62191: 'Rectangle Linen', 62194: 'Rectangle Linen', 62198: 'Rectangle Linen',
    62204: 'Rectangle Linen', 62208: 'Rectangle Linen', 62211: 'Rectangle Linen', 62214: 'Rectangle Linen',
    62215: 'Rectangle Linen', 62219: 'Rectangle Linen', 62224: 'Rectangle Linen', 62225: 'Rectangle Linen',
    62226: 'Rectangle Linen', 62227: 'Rectangle Linen', 62229: 'Rectangle Linen', 62232: 'Rectangle Linen',
    62235: 'Rectangle Linen', 62236: 'Rectangle Linen', 62237: 'Rectangle Linen', 62238: 'Rectangle Linen',
    62239: 'Rectangle Linen', 62242: 'Rectangle Linen', 62246: 'Rectangle Linen', 62247: 'Rectangle Linen',
    62252: 'Rectangle Linen', 62255: 'Rectangle Linen', 62256: 'Rectangle Linen', 62257: 'Rectangle Linen',
    62263: 'Rectangle Linen', 62265: 'Rectangle Linen', 62267: 'Rectangle Linen', 62268: 'Rectangle Linen',
    62271: 'Rectangle Linen', 62272: 'Rectangle Linen', 62273: 'Rectangle Linen', 62274: 'Rectangle Linen',
    62275: 'Rectangle Linen', 62277: 'Rectangle Linen', 62280: 'Rectangle Linen', 62281: 'Rectangle Linen',
    62282: 'Rectangle Linen', 62283: 'Rectangle Linen', 62287: 'Rectangle Linen', 62288: 'Rectangle Linen',
    62289: 'Rectangle Linen', 62290: 'Rectangle Linen', 62291: 'Rectangle Linen', 62292: 'Rectangle Linen',
    62294: 'Rectangle Linen', 62295: 'Rectangle Linen', 62298: 'Rectangle Linen', 62308: 'Rectangle Linen',
    62312: 'Rectangle Linen', 62315: 'Rectangle Linen', 62319: 'Rectangle Linen', 62321: 'Rectangle Linen',
    62323: 'Rectangle Linen', 62330: 'Rectangle Linen', 62331: 'Rectangle Linen', 62332: 'Rectangle Linen',
    62333: 'Rectangle Linen', 62336: 'Rectangle Linen', 62337: 'Rectangle Linen', 62338: 'Rectangle Linen',
    62339: 'Rectangle Linen', 62399: 'Rectangle Linen', 62401: 'Rectangle Linen', 62403: 'Rectangle Linen',
    62426: 'Rectangle Linen', 62429: 'Rectangle Linen', 65545: 'Rectangle Linen', 2857: 'Concession Equipment',
    3290: 'Concession Equipment', 3727: 'Concession Equipment', 3902: 'Concession Equipment', 62468: 'Concession Equipment',
    62475: 'Concession Equipment', 62479: 'Concession Equipment', 62535: 'Concession Equipment', 62633: 'Concession Equipment',
    62634: 'Concession Equipment', 62636: 'Concession Equipment', 62637: 'Concession Equipment', 62651: 'Concession Equipment',
    62652: 'Concession Equipment', 62653: 'Concession Equipment', 62654: 'Concession Equipment', 63791: 'Concession Equipment',
    63793: 'Concession Equipment', 63806: 'Concession Equipment', 66715: 'Concession Equipment', 68317: 'Concession Equipment',
    68318: 'Concession Equipment', 68320: 'Concession Equipment', 68321: 'Concession Equipment', 68322: 'Concession Equipment',
    68332: 'Concession Equipment', 63278: 'Runners and Drapes', 63295: 'Runners and Drapes', 63296: 'Runners and Drapes',
    63297: 'Runners and Drapes', 63298: 'Runners and Drapes', 63299: 'Runners and Drapes', 63300: 'Runners and Drapes',
    63301: 'Runners and Drapes', 63302: 'Runners and Drapes', 63303: 'Runners and Drapes', 63304: 'Runners and Drapes',
    63305: 'Runners and Drapes', 63306: 'Runners and Drapes', 63307: 'Runners and Drapes', 63308: 'Runners and Drapes',
    63309: 'Runners and Drapes', 63310: 'Runners and Drapes', 63311: 'Runners and Drapes', 63313: 'Runners and Drapes',
    63314: 'Runners and Drapes', 63315: 'Runners and Drapes', 63316: 'Runners and Drapes', 63317: 'Runners and Drapes',
    63327: 'Runners and Drapes', 63328: 'Runners and Drapes', 63329: 'Runners and Drapes', 63330: 'Runners and Drapes',
    63331: 'Runners and Drapes', 63332: 'Runners and Drapes', 64836: 'Runners and Drapes', 64837: 'Runners and Drapes',
    66688: 'Runners and Drapes', 61749: 'Other', 61750: 'Other', 61758: 'Other', 61759: 'Other', 61760: 'Other',
    61761: 'Other', 61762: 'Other', 61763: 'Other', 61764: 'Other', 62445: 'Other', 62447: 'Other', 62449: 'Other',
    62451: 'Other', 62452: 'Other', 62233: 'Other', 62234: 'Other', 62284: 'Other', 62285: 'Other', 67139: 'Other',
    67140: 'Other', 99999: 'Other', 1: 'Resale', 3168: 'Resale', 3169: 'Resale', 3903: 'Resale', 64815: 'Resale',
    64816: 'Resale', 64817: 'Resale', 64819: 'Resale', 64824: 'Resale', 64840: 'Resale', 64841: 'Resale',
    64842: 'Resale', 64843: 'Resale', 64847: 'Resale', 64848: 'Resale', 64849: 'Resale', 64852: 'Resale',
    64853: 'Resale', 64854: 'Resale', 64855: 'Resale', 64856: 'Resale', 64857: 'Resale', 64858: 'Resale',
    64860: 'Resale', 64861: 'Resale', 64864: 'Resale', 64865: 'Resale', 64866: 'Resale', 64867: 'Resale',
    64868: 'Resale', 64869: 'Resale', 64874: 'Resale', 64876: 'Resale', 64888: 'Resale', 64889: 'Resale',
    64890: 'Resale', 64891: 'Resale', 64892: 'Resale', 64893: 'Resale', 65604: 'Resale', 65605: 'Resale',
    65606: 'Resale', 65607: 'Resale', 65608: 'Resale', 65609: 'Resale', 64894: 'Resale', 64895: 'Resale',
    64896: 'Resale', 64897: 'Resale', 64898: 'Resale', 64899: 'Resale', 64900: 'Resale', 64901: 'Resale',
    64902: 'Resale', 64904: 'Resale', 64905: 'Resale', 65611: 'Resale', 64906: 'Resale', 64907: 'Resale',
    64908: 'Resale', 64909: 'Resale', 64910: 'Resale', 64911: 'Resale', 64912: 'Resale', 64913: 'Resale',
    64914: 'Resale', 64915: 'Resale', 64916: 'Resale', 64917: 'Resale', 64918: 'Resale', 64919: 'Resale',
    64920: 'Resale', 65495: 'Resale', 65498: 'Resale', 64921: 'Resale', 64922: 'Resale', 64923: 'Resale',
    64924: 'Resale', 64925: 'Resale', 64926: 'Resale', 64927: 'Resale', 64928: 'Resale', 64929: 'Resale',
    64930: 'Resale', 64932: 'Resale', 64933: 'Resale', 64934: 'Resale', 65493: 'Resale', 65496: 'Resale',
    64935: 'Resale', 64936: 'Resale', 64937: 'Resale', 64938: 'Resale', 64939: 'Resale', 64940: 'Resale',
    64941: 'Resale', 64942: 'Resale', 64943: 'Resale', 64944: 'Resale', 64945: 'Resale', 64946: 'Resale',
    64947: 'Resale', 64948: 'Resale', 64949: 'Resale', 65494: 'Resale', 65497: 'Resale', 66742: 'Resale',
    66743: 'Resale', 66747: 'Resale', 65808: 'Resale', 63440: 'Resale'
}

SUBCATEGORY_MAP = {
    4052: 'Sidewalls', 4054: 'Canopy Tops', 4203: 'Navi Lite Tops', 4204: 'Navi Lite Tops', 4213: 'Navi Lite Sidewalls',
    4214: 'Navi Lite Sidewalls', 4292: 'Canopy Tops', 4807: 'HP Sidewalls', 4808: 'HP Sidewalls', 60526: 'Kedar Sidewalls',
    60528: 'Kedar Sidewalls', 62706: 'HP Tops', 62707: 'HP Tops', 62708: 'HP Tops', 62709: 'HP Tops', 62711: 'HP Tops',
    62714: 'HP Tops', 62715: 'HP Sidewalls', 62719: 'HP Sidewalls', 62723: 'HP Sidewalls', 62727: 'HP Sidewalls',
    62731: 'HP Sidewalls', 62735: 'HP Sidewalls', 62737: 'HP Sidewalls', 62745: 'HP Sidewalls', 62749: 'HP Sidewalls',
    62750: 'HP Sidewalls', 62753: 'HP Sidewalls', 62755: 'HP Sidewalls', 62757: 'HP Sidewalls', 62761: 'HP Sidewalls',
    62762: 'HP Sidewalls', 62763: 'HP Sidewalls', 62769: 'HP Sidewalls', 62770: 'HP Sidewalls', 62773: 'HP Sidewalls',
    62781: 'HP Sidewalls', 62782: 'HP Sidewalls', 62805: 'Navi Tops', 62806: 'Navi Tops', 62807: 'Navi Tops',
    62808: 'Navi Tops', 62809: 'Navi Tops', 62810: 'Navi Tops', 62853: 'Mesh Sidewalls', 62857: 'STD Sidewalls',
    62858: 'STD Sidewalls', 62859: 'STD Sidewalls', 62861: 'STD Sidewalls', 62862: 'STD Sidewalls', 62864: 'STD Sidewalls',
    62865: 'STD Sidewalls', 62867: 'STD Sidewalls', 62868: 'STD Sidewalls', 62871: 'Navi Sidewalls', 62872: 'Navi Sidewalls',
    62875: 'STD Sidewalls', 62876: 'STD Sidewalls', 62883: 'Extenders', 62887: 'Extenders', 62891: 'Extenders',
    62894: 'STD Sidewalls', 62895: 'STD Sidewalls', 62896: 'STD Sidewalls', 62797: 'Navi Tops', 62798: 'Navi Tops',
    62900: 'STD Sidewalls', 62901: 'STD Sidewalls', 62902: 'STD Sidewalls', 62904: 'Navi Sidewalls', 62905: 'Navi Sidewalls',
    62906: 'Navi Sidewalls', 65035: 'Navi Tops', 65036: 'Navi Tops', 65037: 'Navi Tops', 65039: 'Navi Tops',
    65367: 'HP Tops', 65119: 'HP Tops', 65446: 'HP Tops', 65449: 'Navi Tops', 65450: 'Navi Tops', 65467: 'Navi Tops',
    65468: 'Navi Tops', 65469: 'Navi Tops', 66324: 'Navi Lite Tops', 66325: 'Navi Tops', 66326: 'Navi Tops',
    67657: 'HP Tops', 65129: 'Canopy Tops', 66363: 'Canopy Tops', 72252: 'Kedar Sidewalls', 72253: 'Kedar Sidewalls',
    72392: 'Navi Lite Tops', 72401: 'Crates', 72402: 'Crates', 72403: 'Crates', 72404: 'Crates', 72405: 'Crates',
    72406: 'Crates', 72407: 'Crates', 72408: 'Crates', 72409: 'Crates', 72410: 'Crates', 72411: 'Crates',
    72412: 'Crates', 62668: 'Canopy Tops', 62669: 'Canopy Tops', 62681: 'Canopy Tops', 62682: 'Canopy Tops',
    62683: 'Canopy Tops', 62684: 'Canopy Tops', 62686: 'Canopy Tops', 62803: 'Canopy Tops', 63851: 'Marquee Tops',
    63852: 'Marquee Tops', 60533: 'Bullhorns', 60537: 'Bullhorns', 60731: 'Bubble Machines', 60735: 'Fog Machines',
    61543: 'Sound Systems', 61545: 'Sound Systems', 61548: 'Sound Systems', 61566: 'Microphones', 61570: 'Microphones',
    61571: 'Microphones', 61572: 'Microphones', 61573: 'Microphones', 63343: 'Fog Machines', 63359: 'Microphones',
    63430: 'Projectors', 63131: 'Table Tops', 63133: 'Table Legs', 65171: 'Table Legs', 65722: 'Table Tops',
    61771: 'Chair Pads', 61772: 'Chair Pads', 61824: '90 Round', 61825: '90 Round', 61826: '90 Round',
    61882: '90 Round', 61883: '90 Round', 61827: '90 Round', 61828: '90 Round', 61830: '90 Round', 61831: '90 Round',
    61832: '90 Round', 61833: '90 Round', 61834: '90 Round', 61835: '90 Round', 61836: '90 Round', 61837: '90 Round',
    61838: '90 Round', 61839: '90 Round', 61840: '90 Round', 61842: '90 Round', 61843: '90 Round', 61846: '90 Round',
    61847: '90 Round', 61848: '90 Round', 61850: '90 Round', 61852: '90 Round', 61854: '90 Round', 61856: '90 Round',
    61858: '90 Round', 61859: '90 Round', 61862: '90 Round', 61863: '90 Round', 61864: '90 Round', 61865: '90 Round',
    61866: '90 Round', 61867: '90 Round', 61868: '90 Round', 61869: '90 Round', 61870: '90 Round', 61871: '90 Round',
    61872: '90 Round', 61873: '90 Round', 61874: '90 Round', 61875: '90 Round', 61876: '90 Round', 61879: '90 Round',
    61880: '90 Round', 61881: '90 Round', 61885: '108 Round', 61886: '108 Round', 61887: '108 Round', 61888: '108 Round',
    61889: '108 Round', 61890: '108 Round', 72595: '108 Round', 61891: '108 Round', 61893: '108 Round', 61895: '108 Round',
    61896: '108 Round', 61901: '108 Round', 61904: '108 Round', 61905: '108 Round', 61908: '108 Round', 61910: '108 Round',
    61912: '108 Round', 61914: '108 Round', 61916: '108 Round', 61921: '108 Round', 61922: '108 Round', 61924: '108 Round',
    61925: '108 Round', 61926: '108 Round', 61927: '108 Round', 61928: '108 Round', 61930: '120 Round', 61931: '120 Round',
    61933: '120 Round', 61934: '120 Round', 61936: '120 Round', 61937: '120 Round', 61939: '120 Round', 61942: '120 Round',
    61943: '120 Round', 61946: '120 Round', 61949: '120 Round', 61950: '120 Round', 61951: '120 Round', 61953: '120 Round',
    61955: '120 Round', 61957: '120 Round', 61958: '120 Round', 61960: '120 Round', 61961: '120 Round', 61962: '120 Round',
    61964: '120 Round', 61965: '120 Round', 61967: '120 Round', 61968: '120 Round', 61970: '120 Round', 61971: '120 Round',
    61972: '120 Round', 61973: '120 Round', 61974: '120 Round', 61975: '120 Round', 61976: '120 Round', 61977: '120 Round',
    61978: '120 Round', 61979: '120 Round', 61981: '132 Round', 61982: '132 Round', 61984: '132 Round', 61985: '132 Round',
    61986: '132 Round', 61989: '132 Round', 61992: '132 Round', 61994: '132 Round', 61996: '132 Round', 61999: '132 Round',
    62003: '132 Round', 62004: '132 Round', 62006: '132 Round', 62010: '132 Round', 62012: '132 Round', 62014: '132 Round',
    62021: '132 Round', 62022: '132 Round', 62024: '132 Round', 62025: '132 Round', 62026: '132 Round', 62027: '132 Round',
    62028: '132 Round', 62029: '132 Round', 62030: '132 Round', 62031: '132 Round', 62032: '132 Round', 62033: '132 Round',
    62034: '132 Round', 62035: '132 Round', 62037: 'Runners', 62038: 'Runners', 62039: 'Runners', 62040: 'Runners',
    62041: 'Runners', 62042: 'Runners', 62045: 'Runners', 62054: 'Runners', 62057: 'Runners', 62065: 'Runners',
    62067: 'Runners', 62077: 'Runners', 62081: 'Runners', 62082: 'Runners', 62083: 'Runners', 62085: 'Caplets',
    62086: 'Caplets', 62087: 'Caplets', 62088: '60x120', 62089: '60x120', 62090: '60x120', 62091: '60x120',
    62092: '60x120', 62093: '60x120', 62094: '60x120', 62095: '60x120', 62096: '60x120', 62098: '60x120',
    62099: '60x120', 62101: '60x120', 62102: '60x120', 62103: '60x120', 62104: '60x120', 62106: '60x120',
    62107: '60x120', 62111: '60x120', 62112: '60x120', 62113: '60x120', 62114: '60x120', 62116: '60x120',
    62117: '60x120', 62118: '60x120', 62119: '60x120', 62121: '60x120', 62122: '60x120', 62126: '60x120',
    62129: '60x120', 62130: '60x120', 62131: '60x120', 62132: '60x120', 62133: '60x120', 62134: '60x120',
    62136: '60x120', 62137: '60x120', 62138: '60x120', 62139: '60x120', 62140: '60x120', 62141: '60x120',
    62142: '60x120', 62187: '90x132', 62188: '90x132', 62189: '90x132', 62191: '90x132', 62194: '90x132',
    62198: '90x132', 62204: '90x132', 62208: '90x132', 62211: '90x132', 62214: '90x132', 62215: '90x132',
    62219: '90x132', 62224: '90x132', 62225: '90x132', 62226: '90x132', 62227: '90x132', 62229: '90x132',
    62232: '90x132', 62235: '90x156', 62236: '90x156', 62237: '90x156', 62238: '90x156', 62239: '90x156',
    62242: '90x156', 62246: '90x156', 62247: '90x156', 62252: '90x156', 62255: '90x156', 62256: '90x156',
    62257: '90x156', 62263: '90x156', 62265: '90x156', 62267: '90x156', 62268: '90x156', 62271: '90x156',
    62272: '90x156', 62273: '90x156', 62274: '90x156', 62275: '90x156', 62277: '90x156', 62280: '90x156',
    62281: '90x156', 62282: '90x156', 62283: '90x156', 62287: '30x96 Conference', 62288: '30x96 Conference',
    62289: '30x96 Conference', 62290: 'Other Rectangle Linen', 62291: '54 Square', 62292: '54 Square',
    62294: '54 Square', 62295: '54 Square', 62298: '54 Square', 62308: '54 Square', 62312: '54 Square',
    62315: '54 Square', 62319: '54 Square', 62321: '54 Square', 62323: '54 Square', 62330: '54 Square',
    62331: '54 Square', 62332: '54 Square', 62333: '54 Square', 62336: '54 Square', 62337: '54 Square',
    62338: '54 Square', 62339: 'Other Rectangle Linen', 62399: '90 Square', 62401: '90 Square',
    62403: '90 Square', 62426: '90 Square', 62429: '90 Square', 65545: 'Runners', 2857: 'Chocolate Fountain',
    3290: 'Beverage Dispensers', 3727: 'Hot Dog Machines', 3902: 'Cheese Warmers', 62468: 'Beverage Dispensers',
    62475: 'Beverage Dispensers', 62479: 'Beverage Dispensers', 62535: 'Hot Dog Machines', 62633: 'Chafers',
    62634: 'Chafers', 62636: 'Chafers', 62637: 'Chafers', 62651: 'Fountains', 62652: 'Fountains',
    62653: 'Fountains', 62654: 'Fountains', 63791: 'Cheese Warmers', 63793: 'Cheese Warmers', 63806: 'Frozen Drink Machines',
    66715: 'Donut Machines', 68317: 'Frozen Drink Machines', 68318: 'Popcorn Machines', 68320: 'Popcorn Machines',
    68321: 'Sno Cone Machines', 68322: 'Cotton Candy Machines', 68332: 'Frozen Drink Machines', 63278: '16 ft',
    63295: '3 ft', 63296: '3 ft', 63297: '3 ft', 63298: '8 ft', 63299: '8 ft', 63300: '8 ft', 63301: '8 ft',
    63302: '8 ft', 63303: '8 ft', 63304: '8 ft', 63305: '8 ft', 63306: '8 ft', 63307: '8 ft', 63308: '8 ft',
    63309: '8 ft', 63310: '8 ft', 63311: '8 ft', 63313: '8 ft', 63314: '8 ft', 63315: '8 ft', 63316: '16 ft',
    63317: '16 ft', 63327: 'Red Runner', 63328: 'Red Runner', 63329: 'Red Runner', 63330: 'Red Runner',
    63331: 'Purple Runner', 63332: 'Purple Runner', 64836: 'Resale Runners', 64837: 'Resale Runners',
    66688: '8 ft', 61749: 'Linens', 61750: 'Stage Skirts', 61758: 'Stage Skirts', 61759: 'Stage Skirts',
    61760: 'Stage Skirts', 61761: 'Stage Skirts', 61762: 'Stage Skirts', 61763: 'Stage Skirts', 61764: 'Stage Skirts',
    62445: 'Spandex Linens', 62447: 'Spandex Linens', 62449: 'Spandex Linens', 62451: 'Spandex Linens',
    62452: 'Spandex Linens', 62233: 'Spandex Linens', 62234: 'Spandex Linens', 62284: 'Spandex Linens',
    62285: 'Spandex Linens', 67139: 'Spandex Linens', 67140: 'Spandex Linens', 99999: 'Miscellaneous',
    1: 'Test', 3168: 'Chocolate', 3169: 'Cheese', 3903: 'Cheese', 64815: 'Fog and Bubbles', 64816: 'Fog and Bubbles',
    64817: 'Fog and Bubbles', 64819: 'Fuel', 64824: 'Fuel', 64840: 'Cotton Candy Supplies', 64841: 'Cotton Candy Supplies',
    64842: 'Cotton Candy Supplies', 64843: 'Cotton Candy Supplies', 64847: 'Cotton Candy Supplies', 64848: 'Cotton Candy Supplies',
    64849: 'Cotton Candy Supplies', 64852: 'Popcorn Supplies', 64853: 'Popcorn Supplies', 64854: 'Cheese',
    64855: 'Sno Cone Supplies', 64856: 'Sno Cone Supplies', 64857: 'Sno Cone Supplies', 64858: 'Sno Cone Supplies',
    64860: 'Sno Cone Supplies', 64861: 'Sno Cone Supplies', 64864: 'Frozen Drink Frusheeze', 64865: 'Frozen Drink Frusheeze',
    64866: 'Frozen Drink Frusheeze', 64867: 'Frozen Drink Frusheeze', 64868: 'Frozen Drink Frusheeze', 64869: 'Frozen Drink Frusheeze',
    64874: 'Frozen Drink Frusheeze', 64876: 'Other Resale', 64888: 'Kwik Covers 30 & 36 Round', 64889: 'Kwik Covers 30 & 36 Round',
    64890: 'Kwik Covers 30 & 36 Round', 64891: 'Kwik Covers 30 & 36 Round', 64892: 'Kwik Covers 30 & 36 Round',
    64893: 'Kwik Covers 30 & 36 Round', 65604: 'Kwik Covers 30 & 36 Round', 65605: 'Kwik Covers 30 & 36 Round',
    65606: 'Kwik Covers 30 & 36 Round', 65607: 'Kwik Covers 30 & 36 Round', 65608: 'Kwik Covers 30 & 36 Round',
    65609: 'Kwik Covers 30 & 36 Round', 64894: 'Kwik Covers 4 ft Round', 64895: 'Kwik Covers 4 ft Round',
    64896: 'Kwik Covers 4 ft Round', 64897: 'Kwik Covers 4 ft Round', 64898: 'Kwik Covers 4 ft Round',
    64899: 'Kwik Covers 4 ft Round', 64900: 'Kwik Covers 4 ft Round', 64901: 'Kwik Covers 4 ft Round',
    64902: 'Kwik Covers 4 ft Round', 64904: 'Kwik Covers 4 ft Round', 64905: 'Kwik Covers 4 ft Round',
    65611: 'Kwik Covers 4 ft Banquet White', 64906: 'Kwik Covers 5 ft Round', 64907: 'Kwik Covers 5 ft Round',
    64908: 'Kwik Covers 5 ft Round', 64909: 'Kwik Covers 5 ft Round', 64910: 'Kwik Covers 5 ft Round',
    64911: 'Kwik Covers 5 ft Round', 64912: 'Kwik Covers 5 ft Round', 64913: 'Kwik Covers 5 ft Round',
    64914: 'Kwik Covers 5 ft Round', 64915: 'Kwik Covers 5 ft Round', 64916: 'Kwik Covers 5 ft Round',
    64917: 'Kwik Covers 5 ft Round', 64918: 'Kwik Covers 5 ft Round', 64919: 'Kwik Covers 5 ft Round',
    64920: 'Kwik Covers 5 ft Round', 65495: 'Kwik Covers 5 ft Round', 65498: 'Kwik Covers 5 ft Round',
    64921: 'Kwik Covers 6 ft Banquet', 64922: 'Kwik Covers 6 ft Banquet', 64923: 'Kwik Covers 6 ft Banquet',
    64924: 'Kwik Covers 6 ft Banquet', 64925: 'Kwik Covers 6 ft Banquet', 64926: 'Kwik Covers 6 ft Banquet',
    64927: 'Kwik Covers 6 ft Banquet', 64928: 'Kwik Covers 6 ft Banquet', 64929: 'Kwik Covers 6 ft Banquet',
    64930: 'Kwik Covers 6 ft Banquet', 64932: 'Kwik Covers 6 ft Banquet', 64933: 'Kwik Covers 6 ft Banquet',
    64934: 'Kwik Covers 6 ft Banquet', 65493: 'Kwik Covers 6 ft Banquet', 65496: 'Kwik Covers 6 ft Banquet',
    64935: 'Kwik Covers 8 ft Banquet', 64936: 'Kwik Covers 8 ft Banquet', 64937: 'Kwik Covers 8 ft Banquet',
    64938: 'Kwik Covers 8 ft Banquet', 64939: 'Kwik Covers 8 ft Banquet', 64940: 'Kwik Covers 8 ft Banquet',
    64941: 'Kwik Covers 8 ft Banquet', 64942: 'Kwik Covers 8 ft Banquet', 64943: 'Kwik Covers 8 ft Banquet',
    64944: 'Kwik Covers 8 ft Banquet', 64945: 'Kwik Covers 8 ft Banquet', 64946: 'Kwik Covers 8 ft Banquet',
    64947: 'Kwik Covers 8 ft Banquet', 64948: 'Kwik Covers 8 ft Banquet', 64949: 'Kwik Covers 8 ft Banquet',
    65494: 'Kwik Covers 8 ft Banquet', 65497: 'Kwik Covers 8 ft Banquet', 66742: 'Donut Supplies',
    66743: 'Donut Supplies', 66747: 'Donut Supplies', 65808: 'Sno Cone Supplies', 63440: 'Kwik Covers 4 ft Round'
}

def categorize_item(rental_class_id):
    try:
        return CATEGORY_MAP.get(int(rental_class_id or 0), 'Other')
    except (ValueError, TypeError) as e:
        logging.error(f"Error categorizing item with rental_class_id {rental_class_id}: {e}")
        return 'Other'

def subcategorize_item(category, rental_class_id):
    try:
        rid = int(rental_class_id or 0)
        if category in ['Tent Tops', 'Tables and Chairs', 'Round Linen', 'Rectangle Linen', 
                        'Concession Equipment', 'AV Equipment', 'Runners and Drapes', 
                        'Other', 'Resale']:
            return SUBCATEGORY_MAP.get(rid, 'Unspecified')
        return 'Unspecified'
    except (ValueError, TypeError) as e:
        logging.error(f"Error subcategorizing item with rental_class_id {rental_class_id}: {e}")
        return 'Unspecified'

@tab2_bp.route("/")
def show_tab2():
    logging.debug("Loading /tab2/ endpoint")
    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
            contracts = conn.execute("""
                SELECT DISTINCT last_contract_num, client_name, MAX(date_last_scanned) as scan_date 
                FROM id_item_master 
                WHERE last_contract_num IS NOT NULL 
                GROUP BY last_contract_num
            """).fetchall()
        items = [dict(row) for row in items]
        contract_map = {c["last_contract_num"]: {"client_name": c["client_name"], "scan_date": c["scan_date"]} for c in contracts}

        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_bin_location = request.args.get("bin_location", "").lower().strip()
        filter_last_contract = request.args.get("last_contract_num", "").lower().strip()
        filter_status = request.args.get("status", "").lower().strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name in (item.get("common_name") or "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id in (item.get("tag_id") or "").lower()]
        if filter_bin_location:
            filtered_items = [item for item in filtered_items if filter_bin_location in (item.get("bin_location") or "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract in (item.get("last_contract_num") or "").lower()]
        if filter_status:
            filtered_items = [item for item in filtered_items if filter_status in (item.get("status") or "").lower()]

        category_map = defaultdict(list)
        for item in filtered_items:
            category = categorize_item(item.get("rental_class_num"))
            category_map[category].append(item)

        parent_data = []
        middle_map = defaultdict(dict)
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            middle_map[category] = {
                subcategory: {
                    "subcategory": subcategory,
                    "total": len(items),
                    "on_contract": sum(1 for item in items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in items if item.get("status") == "Ready to Rent")
                }
                for subcategory, items in subcategory_map.items()
            }

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Rendering tab2 with {len(parent_data)} categories")
        for category in middle_map:
            logging.debug(f"Category {category} has subcategories: {list(middle_map[category].keys())}")

        return render_template(
            "tab2.html",
            parent_data=parent_data,
            middle_map=middle_map,
            contract_map=contract_map,
            filter_common_name=filter_common_name,
            filter_tag_id=filter_tag_id,
            filter_bin_location=filter_bin_location,
            filter_last_contract=filter_last_contract,
            filter_status=filter_status
        )
    except Exception as e:
        logging.error(f"Error in show_tab2: {e}")
        return jsonify({"error": str(e)}), 500

@tab2_bp.route("/data", methods=["GET"])
def tab2_data():
    logging.debug("Loading /tab2/data endpoint")
    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
        items = [dict(row) for row in items]

        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_bin_location = request.args.get("bin_location", "").lower().strip()
        filter_last_contract = request.args.get("last_contract_num", "").lower().strip()
        filter_status = request.args.get("status", "").lower().strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name in (item.get("common_name") or "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id in (item.get("tag_id") or "").lower()]
        if filter_bin_location:
            filtered_items = [item for item in filtered_items if filter_bin_location in (item.get("bin_location") or "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract in (item.get("last_contract_num") or "").lower()]
        if filter_status:
            filtered_items = [item for item in filtered_items if filter_status in (item.get("status") or "").lower()]

        category_map = defaultdict(list)
        for item in filtered_items:
            category = categorize_item(item.get("rental_class_num"))
            category_map[category].append(item)

        parent_data = []
        middle_map = defaultdict(dict)
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            middle_map[category] = {
                subcategory: {
                    "subcategory": subcategory,
                    "total": len(items),
                    "on_contract": sum(1 for item in items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in items if item.get("status") == "Ready to Rent")
                }
                for subcategory, items in subcategory_map.items()
            }

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Returning {len(parent_data)} categories for /tab2/data")

        return jsonify({
            "parent_data": parent_data,
            "middle_map": middle_map
        })
    except Exception as e:
        logging.error(f"Error in tab2_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab2_bp.route("/subcat_data", methods=["GET"])
def subcat_data():
    logging.debug("Hit /tab2/subcat_data endpoint")
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 20

    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
        items = [dict(row) for row in items]

        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_bin_location = request.args.get("bin_location", "").lower().strip()
        filter_last_contract = request.args.get("last_contract_num", "").lower().strip()
        filter_status = request.args.get("status", "").lower().strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name in (item.get("common_name") or "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id in (item.get("tag_id") or "").lower()]
        if filter_bin_location:
            filtered_items = [item for item in filtered_items if filter_bin_location in (item.get("bin_location") or "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract in (item.get("last_contract_num") or "").lower()]
        if filter_status:
            filtered_items = [item for item in filtered_items if filter_status in (item.get("status") or "").lower()]

        subcat_items = [
            item for item in filtered_items
            if categorize_item(item.get("rental_class_num")) == category
            and subcategorize_item(category, item.get("rental_class_num")) == subcategory
        ]

        total_items = len(subcat_items)
        total_pages = (total_items + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = subcat_items[start:end]

        logging.debug(f"AJAX: Category: {category}, Subcategory: {subcategory}, Total Items: {total_items}, Page: {page}")

        return jsonify({
            "items": [{
                "tag_id": item.get("tag_id", "N/A"),
                "common_name": item.get("common_name", "N/A"),
                "status": item.get("status", "N/A"),
                "bin_location": item.get("bin_location", "N/A"),
                "quality": item.get("quality", "N/A"),
                "last_contract_num": item.get("last_contract_num", "N/A"),
                "date_last_scanned": item.get("date_last_scanned", "N/A"),
                "last_scanned_by": item.get("last_scanned_by", "Unknown"),
                "notes": item.get("notes", "N/A"),
                "client_name": item.get("client_name", "N/A")
            } for item in paginated_items],
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        logging.error(f"Error in subcat_data: {e}")
        return jsonify({"error": str(e)}), 500