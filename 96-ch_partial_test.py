# Version 1 - August 21, 2024

from opentrons import protocol_api
from opentrons.protocol_api import COLUMN, ALL
from opentrons import types
# points syntax
#p96.aspirate(100, well.bottom(2).move(types.Point(x=-2, y=2, z =-1)))
import math

metadata = {
    'protocolName': 'Demo Protocol to test Partial Column Pickup of Tiprack using A1 and A12 row of pipette',
    'author': 'Anurag Kanase',
    'description': 'This protocol enables to test partial column tip pickup for 96-ch pipette. The protocol is intended to verify Column tip pickup is functional and working '
}
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):

    tiprack = "opentrons_flex_96_filtertiprack_1000ul"
    
    tips = protocol.load_labware(tiprack, "C2", label = "96 Filter Tiprack 1000µL")
    # ✅ Apply a labware (deck) offset to the tiprack in mm (X: left↔right, Y: front↔back, Z: up↔down)
    # Example: shift tiprack +2.0 mm in X, -1.0 mm in Y, and 0.0 mm in Z
    tips.set_offset(x=0.8, y=1.0, z=0.0)

    p96 = protocol.load_instrument('flex_8channel_1000', 'right')

    
    trash = protocol.load_trash_bin("A3")

    protocol.comment("----> Picking up tips from Column 12 to left")
    for start_loc in ["A1", "A2"]:
        
        
        p96.configure_nozzle_layout(
            style=ALL,
            start=start_loc,
            tip_racks=[tips]) 
        
    
        p96.pick_up_tip()
        p96.home()
        protocol.delay(5)
        p96.drop_tip()
        protocol.comment("---- > Picking up tips from Column 1 to right")
    