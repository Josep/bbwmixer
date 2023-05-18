#include "resource_table_empty.h"
#include "readmidi.h"

void main(void) {
    /* MIDI2IN P9.42 GPIO0_7 0x964*/
    initialize();
    while(1) {
        readmidi();
    }
}
