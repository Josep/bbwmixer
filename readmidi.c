#include "readmidi.h"

#define GPIO0_REGS 0x44e07000
#define GPIO0_DATAIN GPIO0_REGS | 0x138
#define GPIO0_OE GPIO0_REGS | 0x134
#define BITLENGTH 6400
#define BITLENGTHHALF 3200
#define DRAM2 0x10000
#define INCRIBUF {if (ibuf >= bufend) ibuf = bufstart;}

#ifdef PRUN0
#define BUFSTART 0x1004
#define BUFEND 0x1fd8
#define CFGGPIOPIN 0x44e10808
#define CLEARPMAO 0
#define POSIESCR 8
#define POSILECT 0x0c
#define CFGCTRLADDR 0x22000
#define MIDIINPIN 2
#endif
#ifdef PRUN1
#define BUFSTART 0x20
#define BUFEND 0xff4
#define CFGGPIOPIN 0x44e10964
#define CLEARPMAO 1
#define POSIESCR 0
#define POSILECT 4
#define CFGCTRLADDR 0x24000
#define MIDIINPIN 7
#endif

uint32_t inpin;
volatile uint32_t *cfgaddr;
volatile uint32_t *inaddr;
volatile uint32_t *debug;
volatile uint32_t *errstart, *errstop;
volatile uint8_t *shram = (uint8_t *) DRAM2;
volatile uint32_t *cfgctrl, *counter;
volatile uint32_t val32;
uint32_t bufstart = BUFSTART;
uint32_t bufend = BUFEND;
uint32_t ibuf;
uint32_t *iescr;
uint32_t *ilect;
uint8_t runstatus = 0;
uint8_t sysexownstatus = 0;

void init_interrupt() {
#ifdef PRUN1
    uint32_t *addr = (uint32_t *) (DRAM2+0xff8);
    *addr = 0xff;
#endif
}

void activate_interrupt(uint8_t command) {
#ifdef PRUN1
    uint32_t *addr = (uint32_t *) (DRAM2+0xff8);
    *addr = command;
#endif
}

void clearcycles() {
    /* PRU_CTRL.CONTROL_bit.COUNTER_ENABLE = 0 */
    val32 = ~(1<<3);
    *cfgctrl &= val32;
    /* PRU_CTRL.CYCLE = 0 */
    *counter = 0;
    /* PRU_CTRL.CONTROL_bit.COUNTER_ENABLE */
    val32 = (1<<3);
    *cfgctrl |= val32;
}

uint8_t readbyte() {
    uint32_t v32, vin;
    uint8_t byte = 0;
    /* step 1: at least 2 readings with 1 */
    while(1) {
        v32 = *inaddr;
        vin = v32 & inpin;
        if  (vin==inpin) {
            v32 = *inaddr;
            vin = v32 & inpin;
            if  (vin==inpin) {
                break;
            }
        }
    }
    /* step 2: search start bit */
    while(1) {
        v32 = *inaddr;
        vin = v32 & inpin;
            clearcycles();
        if  (vin!=inpin) {
            v32 = *inaddr;
            vin = v32 & inpin;
            if  (vin!=inpin) {
                break;
            }
        }
    }
    while ((*counter) < BITLENGTHHALF){;}
    if (((((*inaddr)&inpin)==inpin)?1:0) == 1) {
        *errstart = (*errstart) + 1;
    }
    while ((*counter) < BITLENGTH){;}
    /* step 3: read bits in the center */
    __delay_cycles(BITLENGTHHALF);
    byte += ((((*inaddr)&inpin)==inpin)?1:0);
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 1;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 2;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 3;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 4;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 5;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 6;
    __delay_cycles(BITLENGTH);
    byte += ((((*inaddr)&inpin)==inpin)?1:0) << 7;
    __delay_cycles(BITLENGTH);
    /* step 4: stop bit */
    if (((((*inaddr)&inpin)==inpin)?1:0) != 1) {
        *errstop = (*errstop) + 1;
    }
    return byte;
}

void readbyteinit(uint32_t cfgctrladdr) {
    volatile uint32_t *datain;
    datain = (uint32_t *)(GPIO0_DATAIN);
    /* step 1: wait for 15 bits without activity */ 
    clearcycles();
    cfgaddr = (uint32_t *) cfgctrladdr;
    while(1) {
        if (((*datain)&inpin)==inpin) {
            __delay_cycles(0);
            if ((*cfgaddr) > (15*BITLENGTH)) {
                break;
            }
        }
        else {
            clearcycles();
        }
    }
}

void initialize() {
    inpin = 1 << MIDIINPIN;
    ibuf = bufstart;
    /* Clear SYSCFG[STANDBY_INIT] to enable OCP master port */
    cfgaddr = (uint32_t *)0x26004;
    val32 = ~(1<<4);
    *cfgaddr &= val32;
    /* Clear PMAO PRU */
    cfgaddr = (uint32_t *)0x26028;
    val32 = ~(1<<CLEARPMAO);
    *cfgaddr &= val32;
    /* MIDIIN PIN */
    cfgaddr = (uint32_t *) CFGGPIOPIN;
    *cfgaddr = 0x000027;
    cfgaddr = (uint32_t *) (GPIO0_OE);
    *cfgaddr |= inpin;
    /* indice escritura de midiin */
    iescr = (uint32_t *) &shram[POSIESCR]; 
    *iescr = bufstart;
    /* indice lectura de midiin */
    ilect = (uint32_t *) &shram[POSILECT]; 
    *ilect = bufstart;
    /* clear buffer */
    bzero((void *)&shram[bufstart], bufend-bufstart);
    /* inaddr */
    inaddr = (uint32_t *) (GPIO0_DATAIN);
    /* errors startbit */
    errstart = (uint32_t *) &shram[0x2fcc];
    *errstart = 0;
    /* errors stopbit */
    errstop = (uint32_t *) &shram[0x2fd0];
    *errstop = 0;
    /* cycle counter */
    cfgctrl = (uint32_t *) CFGCTRLADDR;
    counter = (uint32_t *) (CFGCTRLADDR + 0x0c);
    /* debug */
    debug = (uint32_t *) &shram[0x1c];
    /* other inits */
    readbyteinit(CFGCTRLADDR + 0x0c);
    init_interrupt();
}

void readmidi() {
    uint8_t byte;
    uint8_t byte2;
    uint8_t sele;
    byte = readbyte();
    if ((byte >> 7) & 1) {
        shram[ibuf++] = byte;
	INCRIBUF
        sele = (byte >> 4) & 0x0f;
        if ((sele==0x09)||(sele==0x0B)||(sele==0x0E)) {
            runstatus = byte;
        }
        if ((byte>=0xf0)&&(byte<=0xf7)) {
            runstatus = 0;
        }
        if ((sele==0x08)||(sele==0x09)||(sele==0x0A)||(sele==0x0B)||(sele==0x0E)||(byte==0xf2)) {
            shram[ibuf++] = readbyte();
	    INCRIBUF
            shram[ibuf++] = readbyte();
	    INCRIBUF
        }
        else {
            if ((sele==0x0c)||(sele==0x0d)||(byte==0xf1)||(byte==0xf3)) {
                shram[ibuf++] = readbyte();
		INCRIBUF
            }
            else {
                if (byte==0xf0) {
                    sysexownstatus = 0;
                    *debug = 0xffffffff;
                    while(1) {
                        sysexownstatus++;
                        byte2 = readbyte();
                        shram[ibuf++] = byte2;
			INCRIBUF
                        if ((byte2 == 0x7d) && (sysexownstatus == 1)) {
                            sysexownstatus = 0x80;
                        }
                        if (sysexownstatus == 0x84) {
                            *debug = byte2;
			    activate_interrupt(byte2);
                        }
                        if (byte2==0xf7) {
                            break;
                        }
                        if (byte2&0x80) {
                            uint32_t verr;
                            verr = ((*errstart) >> 24) & 0xff;
                            verr++;
                            verr &= 0xff;
                            verr = (verr << 24) + ((*errstart) & 0xFFFFFF);
                            *errstart = verr;
                            break;
                        }
                    }
                }
            }
        }
    }
    else {
        if (runstatus != 0) {
            shram[ibuf++] = runstatus;
	    INCRIBUF
            shram[ibuf++] = byte;
	    INCRIBUF
            shram[ibuf++] = readbyte();
	    INCRIBUF
        }
    }
    *iescr = ibuf;
}
