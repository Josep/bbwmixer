hacer: midi2in.pru1.out

midi2in.pru1.out: midi2in.pru1.c readmidi.c readmidi.h
	@clpru midi2in.pru1.c readmidi.c --include_path=/var/lib/cloud9/common --include_path=/usr/lib/ti/pru-software-support-package/include --include_path=/usr/lib/ti/pru-software-support-package/include/am335x --include_path=/usr/share/ti/starterware/include --include_path=/usr/share/ti/starterware/include/hw --include_path=/usr/share/ti/cgt-pru/include -DCHIP=am335x -DCHIP_IS_am335x -DMODEL=TI_AM335x_BeagleBone -DPROC=pru -DPRUN=1 -DPRUN1 -v3 -O2 --printf_support=minimal --display_error_number --endian=little --hardware_mac=on -ppd -ppa --asm_listing --c_src_interlist
	@lnkpru -o midi2in.pru1.out midi2in.pru1.obj readmidi.obj --reread_libs --warn_sections --stack_size=0x100 --heap_size=0x100 -m midi2in.pru1.map -i/usr/share/ti/cgt-pru/lib -i/usr/share/ti/cgt-pru/include /var/lib/cloud9/common/am335x_pru.cmd --library=libc.a --library=/usr/lib/ti/pru-software-support-package/lib/rpmsg_lib.lib

clean:
	@rm -f *.obj midi2in.pru1.out *.asm *.lst *.map *.pp *.bin

upload:
	@echo stop > /sys/class/remoteproc/remoteproc2/state || echo "couldn't stop PRU1"
	@cp midi2in.pru1.out /lib/firmware/am335x-pru1-fw
	@/var/lib/cloud9/common/write_init_pins.sh /lib/firmware/am335x-pru1-fw
	@echo start > /sys/class/remoteproc/remoteproc2/state
