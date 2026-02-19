.text
.org 0x0
! sys_add_r_r_zero
test_sys_add_r_r_zero:
	add r0,r1
.org 0x20
! sys_add_r_r_normal
test_sys_add_r_r_normal:
	add r0,r1
.org 0x40
! sys_add_r_r_carry
test_sys_add_r_r_carry:
	add r0,r1
.org 0x60
! sys_add_r_r_pos_ovf
test_sys_add_r_r_pos_ovf:
	add r0,r1
.org 0x80
! sys_add_r_r_neg_ovf
test_sys_add_r_r_neg_ovf:
	add r0,r1
.org 0xa0
! sys_add_r_r_carry_ovf
test_sys_add_r_r_carry_ovf:
	add r0,r1
.org 0xc0
! sys_add_r_r_allones
test_sys_add_r_r_allones:
	add r0,r1
.org 0xe0
! sys_sub_r_r_zero
test_sys_sub_r_r_zero:
	sub r0,r1
.org 0x100
! sys_sub_r_r_normal
test_sys_sub_r_r_normal:
	sub r0,r1
.org 0x120
! sys_sub_r_r_carry
test_sys_sub_r_r_carry:
	sub r0,r1
.org 0x140
! sys_sub_r_r_pos_ovf
test_sys_sub_r_r_pos_ovf:
	sub r0,r1
.org 0x160
! sys_sub_r_r_neg_ovf
test_sys_sub_r_r_neg_ovf:
	sub r0,r1
.org 0x180
! sys_sub_r_r_carry_ovf
test_sys_sub_r_r_carry_ovf:
	sub r0,r1
.org 0x1a0
! sys_sub_r_r_allones
test_sys_sub_r_r_allones:
	sub r0,r1
.org 0x1c0
! sys_and_r_r_zero
test_sys_and_r_r_zero:
	and r0,r1
.org 0x1e0
! sys_and_r_r_normal
test_sys_and_r_r_normal:
	and r0,r1
.org 0x200
! sys_and_r_r_carry
test_sys_and_r_r_carry:
	and r0,r1
.org 0x220
! sys_and_r_r_pos_ovf
test_sys_and_r_r_pos_ovf:
	and r0,r1
.org 0x240
! sys_and_r_r_neg_ovf
test_sys_and_r_r_neg_ovf:
	and r0,r1
.org 0x260
! sys_and_r_r_carry_ovf
test_sys_and_r_r_carry_ovf:
	and r0,r1
.org 0x280
! sys_and_r_r_allones
test_sys_and_r_r_allones:
	and r0,r1
.org 0x2a0
! sys_or_r_r_zero
test_sys_or_r_r_zero:
	or r0,r1
.org 0x2c0
! sys_or_r_r_normal
test_sys_or_r_r_normal:
	or r0,r1
.org 0x2e0
! sys_or_r_r_carry
test_sys_or_r_r_carry:
	or r0,r1
.org 0x300
! sys_or_r_r_pos_ovf
test_sys_or_r_r_pos_ovf:
	or r0,r1
.org 0x320
! sys_or_r_r_neg_ovf
test_sys_or_r_r_neg_ovf:
	or r0,r1
.org 0x340
! sys_or_r_r_carry_ovf
test_sys_or_r_r_carry_ovf:
	or r0,r1
.org 0x360
! sys_or_r_r_allones
test_sys_or_r_r_allones:
	or r0,r1
.org 0x380
! sys_xor_r_r_zero
test_sys_xor_r_r_zero:
	xor r0,r1
.org 0x3a0
! sys_xor_r_r_normal
test_sys_xor_r_r_normal:
	xor r0,r1
.org 0x3c0
! sys_xor_r_r_carry
test_sys_xor_r_r_carry:
	xor r0,r1
.org 0x3e0
! sys_xor_r_r_pos_ovf
test_sys_xor_r_r_pos_ovf:
	xor r0,r1
.org 0x400
! sys_xor_r_r_neg_ovf
test_sys_xor_r_r_neg_ovf:
	xor r0,r1
.org 0x420
! sys_xor_r_r_carry_ovf
test_sys_xor_r_r_carry_ovf:
	xor r0,r1
.org 0x440
! sys_xor_r_r_allones
test_sys_xor_r_r_allones:
	xor r0,r1
.org 0x460
! sys_cp_r_r_zero
test_sys_cp_r_r_zero:
	cp r0,r1
.org 0x480
! sys_cp_r_r_normal
test_sys_cp_r_r_normal:
	cp r0,r1
.org 0x4a0
! sys_cp_r_r_carry
test_sys_cp_r_r_carry:
	cp r0,r1
.org 0x4c0
! sys_cp_r_r_pos_ovf
test_sys_cp_r_r_pos_ovf:
	cp r0,r1
.org 0x4e0
! sys_cp_r_r_neg_ovf
test_sys_cp_r_r_neg_ovf:
	cp r0,r1
.org 0x500
! sys_cp_r_r_carry_ovf
test_sys_cp_r_r_carry_ovf:
	cp r0,r1
.org 0x520
! sys_cp_r_r_allones
test_sys_cp_r_r_allones:
	cp r0,r1
.org 0x540
! sys_add_r_im_normal
test_sys_add_r_im_normal:
	add r0,#0x5678
.org 0x560
! sys_add_r_im_carry
test_sys_add_r_im_carry:
	add r0,#0x0001
.org 0x580
! sys_sub_r_im_normal
test_sys_sub_r_im_normal:
	sub r0,#0x5678
.org 0x5a0
! sys_sub_r_im_carry
test_sys_sub_r_im_carry:
	sub r0,#0x0001
.org 0x5c0
! sys_and_r_im_normal
test_sys_and_r_im_normal:
	and r0,#0x5678
.org 0x5e0
! sys_and_r_im_carry
test_sys_and_r_im_carry:
	and r0,#0x0001
.org 0x600
! sys_or_r_im_normal
test_sys_or_r_im_normal:
	or r0,#0x5678
.org 0x620
! sys_or_r_im_carry
test_sys_or_r_im_carry:
	or r0,#0x0001
.org 0x640
! sys_xor_r_im_normal
test_sys_xor_r_im_normal:
	xor r0,#0x5678
.org 0x660
! sys_xor_r_im_carry
test_sys_xor_r_im_carry:
	xor r0,#0x0001
.org 0x680
! sys_cp_r_im_normal
test_sys_cp_r_im_normal:
	cp r0,#0x5678
.org 0x6a0
! sys_cp_r_im_carry
test_sys_cp_r_im_carry:
	cp r0,#0x0001
.org 0x6c0
! sys_add_r_ir_normal
test_sys_add_r_ir_normal:
	add r0,@r2
.org 0x6e0
! sys_add_r_ir_carry
test_sys_add_r_ir_carry:
	add r0,@r2
.org 0x700
! sys_sub_r_ir_normal
test_sys_sub_r_ir_normal:
	sub r0,@r2
.org 0x720
! sys_sub_r_ir_carry
test_sys_sub_r_ir_carry:
	sub r0,@r2
.org 0x740
! sys_and_r_ir_normal
test_sys_and_r_ir_normal:
	and r0,@r2
.org 0x760
! sys_and_r_ir_carry
test_sys_and_r_ir_carry:
	and r0,@r2
.org 0x780
! sys_or_r_ir_normal
test_sys_or_r_ir_normal:
	or r0,@r2
.org 0x7a0
! sys_or_r_ir_carry
test_sys_or_r_ir_carry:
	or r0,@r2
.org 0x7c0
! sys_xor_r_ir_normal
test_sys_xor_r_ir_normal:
	xor r0,@r2
.org 0x7e0
! sys_xor_r_ir_carry
test_sys_xor_r_ir_carry:
	xor r0,@r2
.org 0x800
! sys_cp_r_ir_normal
test_sys_cp_r_ir_normal:
	cp r0,@r2
.org 0x820
! sys_cp_r_ir_carry
test_sys_cp_r_ir_carry:
	cp r0,@r2
.org 0x840
! sys_add_r_da_normal
test_sys_add_r_da_normal:
	add r0,0x0400
.org 0x860
! sys_add_r_da_carry
test_sys_add_r_da_carry:
	add r0,0x0400
.org 0x880
! sys_sub_r_da_normal
test_sys_sub_r_da_normal:
	sub r0,0x0400
.org 0x8a0
! sys_sub_r_da_carry
test_sys_sub_r_da_carry:
	sub r0,0x0400
.org 0x8c0
! sys_and_r_da_normal
test_sys_and_r_da_normal:
	and r0,0x0400
.org 0x8e0
! sys_and_r_da_carry
test_sys_and_r_da_carry:
	and r0,0x0400
.org 0x900
! sys_or_r_da_normal
test_sys_or_r_da_normal:
	or r0,0x0400
.org 0x920
! sys_or_r_da_carry
test_sys_or_r_da_carry:
	or r0,0x0400
.org 0x940
! sys_xor_r_da_normal
test_sys_xor_r_da_normal:
	xor r0,0x0400
.org 0x960
! sys_xor_r_da_carry
test_sys_xor_r_da_carry:
	xor r0,0x0400
.org 0x980
! sys_cp_r_da_normal
test_sys_cp_r_da_normal:
	cp r0,0x0400
.org 0x9a0
! sys_cp_r_da_carry
test_sys_cp_r_da_carry:
	cp r0,0x0400
.org 0x9c0
! sys_addb_r_r_zero
test_sys_addb_r_r_zero:
	addb rh0,rh1
.org 0x9e0
! sys_addb_r_r_normal
test_sys_addb_r_r_normal:
	addb rh0,rh1
.org 0xa00
! sys_addb_r_r_carry
test_sys_addb_r_r_carry:
	addb rh0,rh1
.org 0xa20
! sys_addb_r_r_pos_ovf
test_sys_addb_r_r_pos_ovf:
	addb rh0,rh1
.org 0xa40
! sys_addb_r_r_neg_ovf
test_sys_addb_r_r_neg_ovf:
	addb rh0,rh1
.org 0xa60
! sys_addb_r_r_carry_ovf
test_sys_addb_r_r_carry_ovf:
	addb rh0,rh1
.org 0xa80
! sys_addb_r_r_allones
test_sys_addb_r_r_allones:
	addb rh0,rh1
.org 0xaa0
! sys_subb_r_r_zero
test_sys_subb_r_r_zero:
	subb rh0,rh1
.org 0xac0
! sys_subb_r_r_normal
test_sys_subb_r_r_normal:
	subb rh0,rh1
.org 0xae0
! sys_subb_r_r_carry
test_sys_subb_r_r_carry:
	subb rh0,rh1
.org 0xb00
! sys_subb_r_r_pos_ovf
test_sys_subb_r_r_pos_ovf:
	subb rh0,rh1
.org 0xb20
! sys_subb_r_r_neg_ovf
test_sys_subb_r_r_neg_ovf:
	subb rh0,rh1
.org 0xb40
! sys_subb_r_r_carry_ovf
test_sys_subb_r_r_carry_ovf:
	subb rh0,rh1
.org 0xb60
! sys_subb_r_r_allones
test_sys_subb_r_r_allones:
	subb rh0,rh1
.org 0xb80
! sys_andb_r_r_zero
test_sys_andb_r_r_zero:
	andb rh0,rh1
.org 0xba0
! sys_andb_r_r_normal
test_sys_andb_r_r_normal:
	andb rh0,rh1
.org 0xbc0
! sys_andb_r_r_carry
test_sys_andb_r_r_carry:
	andb rh0,rh1
.org 0xbe0
! sys_andb_r_r_pos_ovf
test_sys_andb_r_r_pos_ovf:
	andb rh0,rh1
.org 0xc00
! sys_andb_r_r_neg_ovf
test_sys_andb_r_r_neg_ovf:
	andb rh0,rh1
.org 0xc20
! sys_andb_r_r_carry_ovf
test_sys_andb_r_r_carry_ovf:
	andb rh0,rh1
.org 0xc40
! sys_andb_r_r_allones
test_sys_andb_r_r_allones:
	andb rh0,rh1
.org 0xc60
! sys_orb_r_r_zero
test_sys_orb_r_r_zero:
	orb rh0,rh1
.org 0xc80
! sys_orb_r_r_normal
test_sys_orb_r_r_normal:
	orb rh0,rh1
.org 0xca0
! sys_orb_r_r_carry
test_sys_orb_r_r_carry:
	orb rh0,rh1
.org 0xcc0
! sys_orb_r_r_pos_ovf
test_sys_orb_r_r_pos_ovf:
	orb rh0,rh1
.org 0xce0
! sys_orb_r_r_neg_ovf
test_sys_orb_r_r_neg_ovf:
	orb rh0,rh1
.org 0xd00
! sys_orb_r_r_carry_ovf
test_sys_orb_r_r_carry_ovf:
	orb rh0,rh1
.org 0xd20
! sys_orb_r_r_allones
test_sys_orb_r_r_allones:
	orb rh0,rh1
.org 0xd40
! sys_xorb_r_r_zero
test_sys_xorb_r_r_zero:
	xorb rh0,rh1
.org 0xd60
! sys_xorb_r_r_normal
test_sys_xorb_r_r_normal:
	xorb rh0,rh1
.org 0xd80
! sys_xorb_r_r_carry
test_sys_xorb_r_r_carry:
	xorb rh0,rh1
.org 0xda0
! sys_xorb_r_r_pos_ovf
test_sys_xorb_r_r_pos_ovf:
	xorb rh0,rh1
.org 0xdc0
! sys_xorb_r_r_neg_ovf
test_sys_xorb_r_r_neg_ovf:
	xorb rh0,rh1
.org 0xde0
! sys_xorb_r_r_carry_ovf
test_sys_xorb_r_r_carry_ovf:
	xorb rh0,rh1
.org 0xe00
! sys_xorb_r_r_allones
test_sys_xorb_r_r_allones:
	xorb rh0,rh1
.org 0xe20
! sys_cpb_r_r_zero
test_sys_cpb_r_r_zero:
	cpb rh0,rh1
.org 0xe40
! sys_cpb_r_r_normal
test_sys_cpb_r_r_normal:
	cpb rh0,rh1
.org 0xe60
! sys_cpb_r_r_carry
test_sys_cpb_r_r_carry:
	cpb rh0,rh1
.org 0xe80
! sys_cpb_r_r_pos_ovf
test_sys_cpb_r_r_pos_ovf:
	cpb rh0,rh1
.org 0xea0
! sys_cpb_r_r_neg_ovf
test_sys_cpb_r_r_neg_ovf:
	cpb rh0,rh1
.org 0xec0
! sys_cpb_r_r_carry_ovf
test_sys_cpb_r_r_carry_ovf:
	cpb rh0,rh1
.org 0xee0
! sys_cpb_r_r_allones
test_sys_cpb_r_r_allones:
	cpb rh0,rh1
.org 0xf00
! sys_addb_r_im_normal
test_sys_addb_r_im_normal:
	addb rh0,#0x34
.org 0xf20
! sys_addb_r_im_carry
test_sys_addb_r_im_carry:
	addb rh0,#0x01
.org 0xf40
! sys_subb_r_im_normal
test_sys_subb_r_im_normal:
	subb rh0,#0x34
.org 0xf60
! sys_subb_r_im_carry
test_sys_subb_r_im_carry:
	subb rh0,#0x01
.org 0xf80
! sys_andb_r_im_normal
test_sys_andb_r_im_normal:
	andb rh0,#0x34
.org 0xfa0
! sys_andb_r_im_carry
test_sys_andb_r_im_carry:
	andb rh0,#0x01
.org 0xfc0
! sys_orb_r_im_normal
test_sys_orb_r_im_normal:
	orb rh0,#0x34
.org 0xfe0
! sys_orb_r_im_carry
test_sys_orb_r_im_carry:
	orb rh0,#0x01
.org 0x1000
! sys_xorb_r_im_normal
test_sys_xorb_r_im_normal:
	xorb rh0,#0x34
.org 0x1020
! sys_xorb_r_im_carry
test_sys_xorb_r_im_carry:
	xorb rh0,#0x01
.org 0x1040
! sys_cpb_r_im_normal
test_sys_cpb_r_im_normal:
	cpb rh0,#0x34
.org 0x1060
! sys_cpb_r_im_carry
test_sys_cpb_r_im_carry:
	cpb rh0,#0x01
.org 0x1080
! sys_addl_rr_rr_zero
test_sys_addl_rr_rr_zero:
	addl rr0,rr2
.org 0x10a0
! sys_addl_rr_rr_normal
test_sys_addl_rr_rr_normal:
	addl rr0,rr2
.org 0x10c0
! sys_addl_rr_rr_carry
test_sys_addl_rr_rr_carry:
	addl rr0,rr2
.org 0x10e0
! sys_addl_rr_rr_pos_ovf
test_sys_addl_rr_rr_pos_ovf:
	addl rr0,rr2
.org 0x1100
! sys_addl_rr_rr_max
test_sys_addl_rr_rr_max:
	addl rr0,rr2
.org 0x1120
! sys_subl_rr_rr_zero
test_sys_subl_rr_rr_zero:
	subl rr0,rr2
.org 0x1140
! sys_subl_rr_rr_normal
test_sys_subl_rr_rr_normal:
	subl rr0,rr2
.org 0x1160
! sys_subl_rr_rr_carry
test_sys_subl_rr_rr_carry:
	subl rr0,rr2
.org 0x1180
! sys_subl_rr_rr_pos_ovf
test_sys_subl_rr_rr_pos_ovf:
	subl rr0,rr2
.org 0x11a0
! sys_subl_rr_rr_max
test_sys_subl_rr_rr_max:
	subl rr0,rr2
.org 0x11c0
! sys_cpl_rr_rr_zero
test_sys_cpl_rr_rr_zero:
	cpl rr0,rr2
.org 0x11e0
! sys_cpl_rr_rr_normal
test_sys_cpl_rr_rr_normal:
	cpl rr0,rr2
.org 0x1200
! sys_cpl_rr_rr_carry
test_sys_cpl_rr_rr_carry:
	cpl rr0,rr2
.org 0x1220
! sys_cpl_rr_rr_pos_ovf
test_sys_cpl_rr_rr_pos_ovf:
	cpl rr0,rr2
.org 0x1240
! sys_cpl_rr_rr_max
test_sys_cpl_rr_rr_max:
	cpl rr0,rr2
.org 0x1260
! sys_adc_r_r_zero_c0
test_sys_adc_r_r_zero_c0:
	adc r0,r1
.org 0x1280
! sys_adc_r_r_zero_c1
test_sys_adc_r_r_zero_c1:
	adc r0,r1
.org 0x12a0
! sys_adc_r_r_normal_c0
test_sys_adc_r_r_normal_c0:
	adc r0,r1
.org 0x12c0
! sys_adc_r_r_normal_c1
test_sys_adc_r_r_normal_c1:
	adc r0,r1
.org 0x12e0
! sys_adc_r_r_carry_c0
test_sys_adc_r_r_carry_c0:
	adc r0,r1
.org 0x1300
! sys_adc_r_r_carry_c1
test_sys_adc_r_r_carry_c1:
	adc r0,r1
.org 0x1320
! sys_adc_r_r_max_c0
test_sys_adc_r_r_max_c0:
	adc r0,r1
.org 0x1340
! sys_adc_r_r_max_c1
test_sys_adc_r_r_max_c1:
	adc r0,r1
.org 0x1360
! sys_adc_r_r_half_c0
test_sys_adc_r_r_half_c0:
	adc r0,r1
.org 0x1380
! sys_adc_r_r_half_c1
test_sys_adc_r_r_half_c1:
	adc r0,r1
.org 0x13a0
! sys_sbc_r_r_zero_c0
test_sys_sbc_r_r_zero_c0:
	sbc r0,r1
.org 0x13c0
! sys_sbc_r_r_zero_c1
test_sys_sbc_r_r_zero_c1:
	sbc r0,r1
.org 0x13e0
! sys_sbc_r_r_normal_c0
test_sys_sbc_r_r_normal_c0:
	sbc r0,r1
.org 0x1400
! sys_sbc_r_r_normal_c1
test_sys_sbc_r_r_normal_c1:
	sbc r0,r1
.org 0x1420
! sys_sbc_r_r_carry_c0
test_sys_sbc_r_r_carry_c0:
	sbc r0,r1
.org 0x1440
! sys_sbc_r_r_carry_c1
test_sys_sbc_r_r_carry_c1:
	sbc r0,r1
.org 0x1460
! sys_sbc_r_r_max_c0
test_sys_sbc_r_r_max_c0:
	sbc r0,r1
.org 0x1480
! sys_sbc_r_r_max_c1
test_sys_sbc_r_r_max_c1:
	sbc r0,r1
.org 0x14a0
! sys_sbc_r_r_half_c0
test_sys_sbc_r_r_half_c0:
	sbc r0,r1
.org 0x14c0
! sys_sbc_r_r_half_c1
test_sys_sbc_r_r_half_c1:
	sbc r0,r1
.org 0x14e0
! sys_adcb_r_r_zero_c0
test_sys_adcb_r_r_zero_c0:
	adcb rh0,rh1
.org 0x1500
! sys_adcb_r_r_zero_c1
test_sys_adcb_r_r_zero_c1:
	adcb rh0,rh1
.org 0x1520
! sys_adcb_r_r_normal_c0
test_sys_adcb_r_r_normal_c0:
	adcb rh0,rh1
.org 0x1540
! sys_adcb_r_r_normal_c1
test_sys_adcb_r_r_normal_c1:
	adcb rh0,rh1
.org 0x1560
! sys_adcb_r_r_carry_c0
test_sys_adcb_r_r_carry_c0:
	adcb rh0,rh1
.org 0x1580
! sys_adcb_r_r_carry_c1
test_sys_adcb_r_r_carry_c1:
	adcb rh0,rh1
.org 0x15a0
! sys_adcb_r_r_max_c0
test_sys_adcb_r_r_max_c0:
	adcb rh0,rh1
.org 0x15c0
! sys_adcb_r_r_max_c1
test_sys_adcb_r_r_max_c1:
	adcb rh0,rh1
.org 0x15e0
! sys_adcb_r_r_half_c0
test_sys_adcb_r_r_half_c0:
	adcb rh0,rh1
.org 0x1600
! sys_adcb_r_r_half_c1
test_sys_adcb_r_r_half_c1:
	adcb rh0,rh1
.org 0x1620
! sys_sbcb_r_r_zero_c0
test_sys_sbcb_r_r_zero_c0:
	sbcb rh0,rh1
.org 0x1640
! sys_sbcb_r_r_zero_c1
test_sys_sbcb_r_r_zero_c1:
	sbcb rh0,rh1
.org 0x1660
! sys_sbcb_r_r_normal_c0
test_sys_sbcb_r_r_normal_c0:
	sbcb rh0,rh1
.org 0x1680
! sys_sbcb_r_r_normal_c1
test_sys_sbcb_r_r_normal_c1:
	sbcb rh0,rh1
.org 0x16a0
! sys_sbcb_r_r_carry_c0
test_sys_sbcb_r_r_carry_c0:
	sbcb rh0,rh1
.org 0x16c0
! sys_sbcb_r_r_carry_c1
test_sys_sbcb_r_r_carry_c1:
	sbcb rh0,rh1
.org 0x16e0
! sys_sbcb_r_r_max_c0
test_sys_sbcb_r_r_max_c0:
	sbcb rh0,rh1
.org 0x1700
! sys_sbcb_r_r_max_c1
test_sys_sbcb_r_r_max_c1:
	sbcb rh0,rh1
.org 0x1720
! sys_sbcb_r_r_half_c0
test_sys_sbcb_r_r_half_c0:
	sbcb rh0,rh1
.org 0x1740
! sys_sbcb_r_r_half_c1
test_sys_sbcb_r_r_half_c1:
	sbcb rh0,rh1
.org 0x1760
! sys_neg_r_zero
test_sys_neg_r_zero:
	neg r0
.org 0x1780
! sys_neg_r_one
test_sys_neg_r_one:
	neg r0
.org 0x17a0
! sys_neg_r_pos_max
test_sys_neg_r_pos_max:
	neg r0
.org 0x17c0
! sys_neg_r_neg_min
test_sys_neg_r_neg_min:
	neg r0
.org 0x17e0
! sys_com_r_zero
test_sys_com_r_zero:
	com r0
.org 0x1800
! sys_com_r_one
test_sys_com_r_one:
	com r0
.org 0x1820
! sys_com_r_pos_max
test_sys_com_r_pos_max:
	com r0
.org 0x1840
! sys_com_r_neg_min
test_sys_com_r_neg_min:
	com r0
.org 0x1860
! sys_clr_r_zero
test_sys_clr_r_zero:
	clr r0
.org 0x1880
! sys_clr_r_one
test_sys_clr_r_one:
	clr r0
.org 0x18a0
! sys_clr_r_pos_max
test_sys_clr_r_pos_max:
	clr r0
.org 0x18c0
! sys_clr_r_neg_min
test_sys_clr_r_neg_min:
	clr r0
.org 0x18e0
! sys_test_r_zero
test_sys_test_r_zero:
	test r0
.org 0x1900
! sys_test_r_one
test_sys_test_r_one:
	test r0
.org 0x1920
! sys_test_r_pos_max
test_sys_test_r_pos_max:
	test r0
.org 0x1940
! sys_test_r_neg_min
test_sys_test_r_neg_min:
	test r0
.org 0x1960
! sys_tset_r_zero
test_sys_tset_r_zero:
	tset r0
.org 0x1980
! sys_tset_r_one
test_sys_tset_r_one:
	tset r0
.org 0x19a0
! sys_tset_r_pos_max
test_sys_tset_r_pos_max:
	tset r0
.org 0x19c0
! sys_tset_r_neg_min
test_sys_tset_r_neg_min:
	tset r0
.org 0x19e0
! sys_negb_r_zero
test_sys_negb_r_zero:
	negb rh0
.org 0x1a00
! sys_negb_r_one
test_sys_negb_r_one:
	negb rh0
.org 0x1a20
! sys_negb_r_pos_max
test_sys_negb_r_pos_max:
	negb rh0
.org 0x1a40
! sys_negb_r_neg_min
test_sys_negb_r_neg_min:
	negb rh0
.org 0x1a60
! sys_comb_r_zero
test_sys_comb_r_zero:
	comb rh0
.org 0x1a80
! sys_comb_r_one
test_sys_comb_r_one:
	comb rh0
.org 0x1aa0
! sys_comb_r_pos_max
test_sys_comb_r_pos_max:
	comb rh0
.org 0x1ac0
! sys_comb_r_neg_min
test_sys_comb_r_neg_min:
	comb rh0
.org 0x1ae0
! sys_clrb_r_zero
test_sys_clrb_r_zero:
	clrb rh0
.org 0x1b00
! sys_clrb_r_one
test_sys_clrb_r_one:
	clrb rh0
.org 0x1b20
! sys_clrb_r_pos_max
test_sys_clrb_r_pos_max:
	clrb rh0
.org 0x1b40
! sys_clrb_r_neg_min
test_sys_clrb_r_neg_min:
	clrb rh0
.org 0x1b60
! sys_testb_r_zero
test_sys_testb_r_zero:
	testb rh0
.org 0x1b80
! sys_testb_r_one
test_sys_testb_r_one:
	testb rh0
.org 0x1ba0
! sys_testb_r_pos_max
test_sys_testb_r_pos_max:
	testb rh0
.org 0x1bc0
! sys_testb_r_neg_min
test_sys_testb_r_neg_min:
	testb rh0
.org 0x1be0
! sys_tsetb_r_zero
test_sys_tsetb_r_zero:
	tsetb rh0
.org 0x1c00
! sys_tsetb_r_one
test_sys_tsetb_r_one:
	tsetb rh0
.org 0x1c20
! sys_tsetb_r_pos_max
test_sys_tsetb_r_pos_max:
	tsetb rh0
.org 0x1c40
! sys_tsetb_r_neg_min
test_sys_tsetb_r_neg_min:
	tsetb rh0
.org 0x1c60
! sys_testl_rr_zero
test_sys_testl_rr_zero:
	testl rr0
.org 0x1c80
! sys_testl_rr_one
test_sys_testl_rr_one:
	testl rr0
.org 0x1ca0
! sys_testl_rr_pos_max
test_sys_testl_rr_pos_max:
	testl rr0
.org 0x1cc0
! sys_testl_rr_neg_min
test_sys_testl_rr_neg_min:
	testl rr0
.org 0x1ce0
! sys_sll_r_one_n1
test_sys_sll_r_one_n1:
	sll r0,#1
.org 0x1d00
! sys_srl_r_one_n1
test_sys_srl_r_one_n1:
	srl r0,#1
.org 0x1d20
! sys_sla_r_one_n1
test_sys_sla_r_one_n1:
	sla r0,#1
.org 0x1d40
! sys_sra_r_one_n1
test_sys_sra_r_one_n1:
	sra r0,#1
.org 0x1d60
! sys_sll_r_one_n4
test_sys_sll_r_one_n4:
	sll r0,#4
.org 0x1d80
! sys_srl_r_one_n4
test_sys_srl_r_one_n4:
	srl r0,#4
.org 0x1da0
! sys_sla_r_one_n4
test_sys_sla_r_one_n4:
	sla r0,#4
.org 0x1dc0
! sys_sra_r_one_n4
test_sys_sra_r_one_n4:
	sra r0,#4
.org 0x1de0
! sys_sll_r_one_n8
test_sys_sll_r_one_n8:
	sll r0,#8
.org 0x1e00
! sys_srl_r_one_n8
test_sys_srl_r_one_n8:
	srl r0,#8
.org 0x1e20
! sys_sla_r_one_n8
test_sys_sla_r_one_n8:
	sla r0,#8
.org 0x1e40
! sys_sra_r_one_n8
test_sys_sra_r_one_n8:
	sra r0,#8
.org 0x1e60
! sys_sll_r_msb_n1
test_sys_sll_r_msb_n1:
	sll r0,#1
.org 0x1e80
! sys_srl_r_msb_n1
test_sys_srl_r_msb_n1:
	srl r0,#1
.org 0x1ea0
! sys_sla_r_msb_n1
test_sys_sla_r_msb_n1:
	sla r0,#1
.org 0x1ec0
! sys_sra_r_msb_n1
test_sys_sra_r_msb_n1:
	sra r0,#1
.org 0x1ee0
! sys_sll_r_msb_n4
test_sys_sll_r_msb_n4:
	sll r0,#4
.org 0x1f00
! sys_srl_r_msb_n4
test_sys_srl_r_msb_n4:
	srl r0,#4
.org 0x1f20
! sys_sla_r_msb_n4
test_sys_sla_r_msb_n4:
	sla r0,#4
.org 0x1f40
! sys_sra_r_msb_n4
test_sys_sra_r_msb_n4:
	sra r0,#4
.org 0x1f60
! sys_sll_r_msb_n8
test_sys_sll_r_msb_n8:
	sll r0,#8
.org 0x1f80
! sys_srl_r_msb_n8
test_sys_srl_r_msb_n8:
	srl r0,#8
.org 0x1fa0
! sys_sla_r_msb_n8
test_sys_sla_r_msb_n8:
	sla r0,#8
.org 0x1fc0
! sys_sra_r_msb_n8
test_sys_sra_r_msb_n8:
	sra r0,#8
.org 0x1fe0
! sys_sll_r_pattern_n1
test_sys_sll_r_pattern_n1:
	sll r0,#1
.org 0x2000
! sys_srl_r_pattern_n1
test_sys_srl_r_pattern_n1:
	srl r0,#1
.org 0x2020
! sys_sla_r_pattern_n1
test_sys_sla_r_pattern_n1:
	sla r0,#1
.org 0x2040
! sys_sra_r_pattern_n1
test_sys_sra_r_pattern_n1:
	sra r0,#1
.org 0x2060
! sys_sll_r_pattern_n4
test_sys_sll_r_pattern_n4:
	sll r0,#4
.org 0x2080
! sys_srl_r_pattern_n4
test_sys_srl_r_pattern_n4:
	srl r0,#4
.org 0x20a0
! sys_sla_r_pattern_n4
test_sys_sla_r_pattern_n4:
	sla r0,#4
.org 0x20c0
! sys_sra_r_pattern_n4
test_sys_sra_r_pattern_n4:
	sra r0,#4
.org 0x20e0
! sys_sll_r_pattern_n8
test_sys_sll_r_pattern_n8:
	sll r0,#8
.org 0x2100
! sys_srl_r_pattern_n8
test_sys_srl_r_pattern_n8:
	srl r0,#8
.org 0x2120
! sys_sla_r_pattern_n8
test_sys_sla_r_pattern_n8:
	sla r0,#8
.org 0x2140
! sys_sra_r_pattern_n8
test_sys_sra_r_pattern_n8:
	sra r0,#8
.org 0x2160
! sys_sllb_r_one_n1
test_sys_sllb_r_one_n1:
	sllb rh0,#1
.org 0x2180
! sys_srlb_r_one_n1
test_sys_srlb_r_one_n1:
	srlb rh0,#1
.org 0x21a0
! sys_slab_r_one_n1
test_sys_slab_r_one_n1:
	slab rh0,#1
.org 0x21c0
! sys_srab_r_one_n1
test_sys_srab_r_one_n1:
	srab rh0,#1
.org 0x21e0
! sys_sllb_r_one_n4
test_sys_sllb_r_one_n4:
	sllb rh0,#4
.org 0x2200
! sys_srlb_r_one_n4
test_sys_srlb_r_one_n4:
	srlb rh0,#4
.org 0x2220
! sys_slab_r_one_n4
test_sys_slab_r_one_n4:
	slab rh0,#4
.org 0x2240
! sys_srab_r_one_n4
test_sys_srab_r_one_n4:
	srab rh0,#4
.org 0x2260
! sys_sllb_r_msb_n1
test_sys_sllb_r_msb_n1:
	sllb rh0,#1
.org 0x2280
! sys_srlb_r_msb_n1
test_sys_srlb_r_msb_n1:
	srlb rh0,#1
.org 0x22a0
! sys_slab_r_msb_n1
test_sys_slab_r_msb_n1:
	slab rh0,#1
.org 0x22c0
! sys_srab_r_msb_n1
test_sys_srab_r_msb_n1:
	srab rh0,#1
.org 0x22e0
! sys_sllb_r_msb_n4
test_sys_sllb_r_msb_n4:
	sllb rh0,#4
.org 0x2300
! sys_srlb_r_msb_n4
test_sys_srlb_r_msb_n4:
	srlb rh0,#4
.org 0x2320
! sys_slab_r_msb_n4
test_sys_slab_r_msb_n4:
	slab rh0,#4
.org 0x2340
! sys_srab_r_msb_n4
test_sys_srab_r_msb_n4:
	srab rh0,#4
.org 0x2360
! sys_sllb_r_pattern_n1
test_sys_sllb_r_pattern_n1:
	sllb rh0,#1
.org 0x2380
! sys_srlb_r_pattern_n1
test_sys_srlb_r_pattern_n1:
	srlb rh0,#1
.org 0x23a0
! sys_slab_r_pattern_n1
test_sys_slab_r_pattern_n1:
	slab rh0,#1
.org 0x23c0
! sys_srab_r_pattern_n1
test_sys_srab_r_pattern_n1:
	srab rh0,#1
.org 0x23e0
! sys_sllb_r_pattern_n4
test_sys_sllb_r_pattern_n4:
	sllb rh0,#4
.org 0x2400
! sys_srlb_r_pattern_n4
test_sys_srlb_r_pattern_n4:
	srlb rh0,#4
.org 0x2420
! sys_slab_r_pattern_n4
test_sys_slab_r_pattern_n4:
	slab rh0,#4
.org 0x2440
! sys_srab_r_pattern_n4
test_sys_srab_r_pattern_n4:
	srab rh0,#4
.org 0x2460
! sys_slll_rr_one_n1
test_sys_slll_rr_one_n1:
	slll rr0,#1
.org 0x2480
! sys_srll_rr_one_n1
test_sys_srll_rr_one_n1:
	srll rr0,#1
.org 0x24a0
! sys_slal_rr_one_n1
test_sys_slal_rr_one_n1:
	slal rr0,#1
.org 0x24c0
! sys_sral_rr_one_n1
test_sys_sral_rr_one_n1:
	sral rr0,#1
.org 0x24e0
! sys_slll_rr_one_n8
test_sys_slll_rr_one_n8:
	slll rr0,#8
.org 0x2500
! sys_srll_rr_one_n8
test_sys_srll_rr_one_n8:
	srll rr0,#8
.org 0x2520
! sys_slal_rr_one_n8
test_sys_slal_rr_one_n8:
	slal rr0,#8
.org 0x2540
! sys_sral_rr_one_n8
test_sys_sral_rr_one_n8:
	sral rr0,#8
.org 0x2560
! sys_slll_rr_msb_n1
test_sys_slll_rr_msb_n1:
	slll rr0,#1
.org 0x2580
! sys_srll_rr_msb_n1
test_sys_srll_rr_msb_n1:
	srll rr0,#1
.org 0x25a0
! sys_slal_rr_msb_n1
test_sys_slal_rr_msb_n1:
	slal rr0,#1
.org 0x25c0
! sys_sral_rr_msb_n1
test_sys_sral_rr_msb_n1:
	sral rr0,#1
.org 0x25e0
! sys_slll_rr_msb_n8
test_sys_slll_rr_msb_n8:
	slll rr0,#8
.org 0x2600
! sys_srll_rr_msb_n8
test_sys_srll_rr_msb_n8:
	srll rr0,#8
.org 0x2620
! sys_slal_rr_msb_n8
test_sys_slal_rr_msb_n8:
	slal rr0,#8
.org 0x2640
! sys_sral_rr_msb_n8
test_sys_sral_rr_msb_n8:
	sral rr0,#8
.org 0x2660
! sys_sda_r_one_l1
test_sys_sda_r_one_l1:
	sda r0,r1
.org 0x2680
! sys_sda_r_msb_l1
test_sys_sda_r_msb_l1:
	sda r0,r1
.org 0x26a0
! sys_sda_r_one_r1
test_sys_sda_r_one_r1:
	sda r0,r1
.org 0x26c0
! sys_sda_r_msb_r1
test_sys_sda_r_msb_r1:
	sda r0,r1
.org 0x26e0
! sys_sda_r_one_l4
test_sys_sda_r_one_l4:
	sda r0,r1
.org 0x2700
! sys_sda_r_msb_l4
test_sys_sda_r_msb_l4:
	sda r0,r1
.org 0x2720
! sys_sda_r_one_r4
test_sys_sda_r_one_r4:
	sda r0,r1
.org 0x2740
! sys_sda_r_msb_r4
test_sys_sda_r_msb_r4:
	sda r0,r1
.org 0x2760
! sys_sdl_r_one_l1
test_sys_sdl_r_one_l1:
	sdl r0,r1
.org 0x2780
! sys_sdl_r_msb_l1
test_sys_sdl_r_msb_l1:
	sdl r0,r1
.org 0x27a0
! sys_sdl_r_one_r1
test_sys_sdl_r_one_r1:
	sdl r0,r1
.org 0x27c0
! sys_sdl_r_msb_r1
test_sys_sdl_r_msb_r1:
	sdl r0,r1
.org 0x27e0
! sys_sdl_r_one_l4
test_sys_sdl_r_one_l4:
	sdl r0,r1
.org 0x2800
! sys_sdl_r_msb_l4
test_sys_sdl_r_msb_l4:
	sdl r0,r1
.org 0x2820
! sys_sdl_r_one_r4
test_sys_sdl_r_one_r4:
	sdl r0,r1
.org 0x2840
! sys_sdl_r_msb_r4
test_sys_sdl_r_msb_r4:
	sdl r0,r1
.org 0x2860
! sys_sdab_r_one_l1
test_sys_sdab_r_one_l1:
	sdab rh0,r1
.org 0x2880
! sys_sdab_r_msb_l1
test_sys_sdab_r_msb_l1:
	sdab rh0,r1
.org 0x28a0
! sys_sdab_r_one_r1
test_sys_sdab_r_one_r1:
	sdab rh0,r1
.org 0x28c0
! sys_sdab_r_msb_r1
test_sys_sdab_r_msb_r1:
	sdab rh0,r1
.org 0x28e0
! sys_sdab_r_one_l4
test_sys_sdab_r_one_l4:
	sdab rh0,r1
.org 0x2900
! sys_sdab_r_msb_l4
test_sys_sdab_r_msb_l4:
	sdab rh0,r1
.org 0x2920
! sys_sdab_r_one_r4
test_sys_sdab_r_one_r4:
	sdab rh0,r1
.org 0x2940
! sys_sdab_r_msb_r4
test_sys_sdab_r_msb_r4:
	sdab rh0,r1
.org 0x2960
! sys_sdlb_r_one_l1
test_sys_sdlb_r_one_l1:
	sdlb rh0,r1
.org 0x2980
! sys_sdlb_r_msb_l1
test_sys_sdlb_r_msb_l1:
	sdlb rh0,r1
.org 0x29a0
! sys_sdlb_r_one_r1
test_sys_sdlb_r_one_r1:
	sdlb rh0,r1
.org 0x29c0
! sys_sdlb_r_msb_r1
test_sys_sdlb_r_msb_r1:
	sdlb rh0,r1
.org 0x29e0
! sys_sdlb_r_one_l4
test_sys_sdlb_r_one_l4:
	sdlb rh0,r1
.org 0x2a00
! sys_sdlb_r_msb_l4
test_sys_sdlb_r_msb_l4:
	sdlb rh0,r1
.org 0x2a20
! sys_sdlb_r_one_r4
test_sys_sdlb_r_one_r4:
	sdlb rh0,r1
.org 0x2a40
! sys_sdlb_r_msb_r4
test_sys_sdlb_r_msb_r4:
	sdlb rh0,r1
.org 0x2a60
! sys_sdal_rr_one_l1
test_sys_sdal_rr_one_l1:
	sdal rr2,r1
.org 0x2a80
! sys_sdal_rr_msb_l1
test_sys_sdal_rr_msb_l1:
	sdal rr2,r1
.org 0x2aa0
! sys_sdal_rr_one_r1
test_sys_sdal_rr_one_r1:
	sdal rr2,r1
.org 0x2ac0
! sys_sdal_rr_msb_r1
test_sys_sdal_rr_msb_r1:
	sdal rr2,r1
.org 0x2ae0
! sys_sdal_rr_one_l4
test_sys_sdal_rr_one_l4:
	sdal rr2,r1
.org 0x2b00
! sys_sdal_rr_msb_l4
test_sys_sdal_rr_msb_l4:
	sdal rr2,r1
.org 0x2b20
! sys_sdal_rr_one_r4
test_sys_sdal_rr_one_r4:
	sdal rr2,r1
.org 0x2b40
! sys_sdal_rr_msb_r4
test_sys_sdal_rr_msb_r4:
	sdal rr2,r1
.org 0x2b60
! sys_sdll_rr_one_l1
test_sys_sdll_rr_one_l1:
	sdll rr2,r1
.org 0x2b80
! sys_sdll_rr_msb_l1
test_sys_sdll_rr_msb_l1:
	sdll rr2,r1
.org 0x2ba0
! sys_sdll_rr_one_r1
test_sys_sdll_rr_one_r1:
	sdll rr2,r1
.org 0x2bc0
! sys_sdll_rr_msb_r1
test_sys_sdll_rr_msb_r1:
	sdll rr2,r1
.org 0x2be0
! sys_sdll_rr_one_l4
test_sys_sdll_rr_one_l4:
	sdll rr2,r1
.org 0x2c00
! sys_sdll_rr_msb_l4
test_sys_sdll_rr_msb_l4:
	sdll rr2,r1
.org 0x2c20
! sys_sdll_rr_one_r4
test_sys_sdll_rr_one_r4:
	sdll rr2,r1
.org 0x2c40
! sys_sdll_rr_msb_r4
test_sys_sdll_rr_msb_r4:
	sdll rr2,r1
.org 0x2c60
! sys_rl_r_one_n1
test_sys_rl_r_one_n1:
	rl r0,#1
.org 0x2c80
! sys_rl_r_one_n2
test_sys_rl_r_one_n2:
	rl r0,#2
.org 0x2ca0
! sys_rl_r_msb_n1
test_sys_rl_r_msb_n1:
	rl r0,#1
.org 0x2cc0
! sys_rl_r_msb_n2
test_sys_rl_r_msb_n2:
	rl r0,#2
.org 0x2ce0
! sys_rl_r_pattern_n1
test_sys_rl_r_pattern_n1:
	rl r0,#1
.org 0x2d00
! sys_rl_r_pattern_n2
test_sys_rl_r_pattern_n2:
	rl r0,#2
.org 0x2d20
! sys_rr_r_one_n1
test_sys_rr_r_one_n1:
	rr r0,#1
.org 0x2d40
! sys_rr_r_one_n2
test_sys_rr_r_one_n2:
	rr r0,#2
.org 0x2d60
! sys_rr_r_msb_n1
test_sys_rr_r_msb_n1:
	rr r0,#1
.org 0x2d80
! sys_rr_r_msb_n2
test_sys_rr_r_msb_n2:
	rr r0,#2
.org 0x2da0
! sys_rr_r_pattern_n1
test_sys_rr_r_pattern_n1:
	rr r0,#1
.org 0x2dc0
! sys_rr_r_pattern_n2
test_sys_rr_r_pattern_n2:
	rr r0,#2
.org 0x2de0
! sys_rlc_r_one_n1_c0
test_sys_rlc_r_one_n1_c0:
	rlc r0,#1
.org 0x2e00
! sys_rlc_r_one_n1_c1
test_sys_rlc_r_one_n1_c1:
	rlc r0,#1
.org 0x2e20
! sys_rlc_r_one_n2_c0
test_sys_rlc_r_one_n2_c0:
	rlc r0,#2
.org 0x2e40
! sys_rlc_r_one_n2_c1
test_sys_rlc_r_one_n2_c1:
	rlc r0,#2
.org 0x2e60
! sys_rlc_r_msb_n1_c0
test_sys_rlc_r_msb_n1_c0:
	rlc r0,#1
.org 0x2e80
! sys_rlc_r_msb_n1_c1
test_sys_rlc_r_msb_n1_c1:
	rlc r0,#1
.org 0x2ea0
! sys_rlc_r_msb_n2_c0
test_sys_rlc_r_msb_n2_c0:
	rlc r0,#2
.org 0x2ec0
! sys_rlc_r_msb_n2_c1
test_sys_rlc_r_msb_n2_c1:
	rlc r0,#2
.org 0x2ee0
! sys_rlc_r_pattern_n1_c0
test_sys_rlc_r_pattern_n1_c0:
	rlc r0,#1
.org 0x2f00
! sys_rlc_r_pattern_n1_c1
test_sys_rlc_r_pattern_n1_c1:
	rlc r0,#1
.org 0x2f20
! sys_rlc_r_pattern_n2_c0
test_sys_rlc_r_pattern_n2_c0:
	rlc r0,#2
.org 0x2f40
! sys_rlc_r_pattern_n2_c1
test_sys_rlc_r_pattern_n2_c1:
	rlc r0,#2
.org 0x2f60
! sys_rrc_r_one_n1_c0
test_sys_rrc_r_one_n1_c0:
	rrc r0,#1
.org 0x2f80
! sys_rrc_r_one_n1_c1
test_sys_rrc_r_one_n1_c1:
	rrc r0,#1
.org 0x2fa0
! sys_rrc_r_one_n2_c0
test_sys_rrc_r_one_n2_c0:
	rrc r0,#2
.org 0x2fc0
! sys_rrc_r_one_n2_c1
test_sys_rrc_r_one_n2_c1:
	rrc r0,#2
.org 0x2fe0
! sys_rrc_r_msb_n1_c0
test_sys_rrc_r_msb_n1_c0:
	rrc r0,#1
.org 0x3000
! sys_rrc_r_msb_n1_c1
test_sys_rrc_r_msb_n1_c1:
	rrc r0,#1
.org 0x3020
! sys_rrc_r_msb_n2_c0
test_sys_rrc_r_msb_n2_c0:
	rrc r0,#2
.org 0x3040
! sys_rrc_r_msb_n2_c1
test_sys_rrc_r_msb_n2_c1:
	rrc r0,#2
.org 0x3060
! sys_rrc_r_pattern_n1_c0
test_sys_rrc_r_pattern_n1_c0:
	rrc r0,#1
.org 0x3080
! sys_rrc_r_pattern_n1_c1
test_sys_rrc_r_pattern_n1_c1:
	rrc r0,#1
.org 0x30a0
! sys_rrc_r_pattern_n2_c0
test_sys_rrc_r_pattern_n2_c0:
	rrc r0,#2
.org 0x30c0
! sys_rrc_r_pattern_n2_c1
test_sys_rrc_r_pattern_n2_c1:
	rrc r0,#2
.org 0x30e0
! sys_rlb_r_one_n1
test_sys_rlb_r_one_n1:
	rlb rh0,#1
.org 0x3100
! sys_rlb_r_one_n2
test_sys_rlb_r_one_n2:
	rlb rh0,#2
.org 0x3120
! sys_rlb_r_msb_n1
test_sys_rlb_r_msb_n1:
	rlb rh0,#1
.org 0x3140
! sys_rlb_r_msb_n2
test_sys_rlb_r_msb_n2:
	rlb rh0,#2
.org 0x3160
! sys_rlb_r_pattern_n1
test_sys_rlb_r_pattern_n1:
	rlb rh0,#1
.org 0x3180
! sys_rlb_r_pattern_n2
test_sys_rlb_r_pattern_n2:
	rlb rh0,#2
.org 0x31a0
! sys_rrb_r_one_n1
test_sys_rrb_r_one_n1:
	rrb rh0,#1
.org 0x31c0
! sys_rrb_r_one_n2
test_sys_rrb_r_one_n2:
	rrb rh0,#2
.org 0x31e0
! sys_rrb_r_msb_n1
test_sys_rrb_r_msb_n1:
	rrb rh0,#1
.org 0x3200
! sys_rrb_r_msb_n2
test_sys_rrb_r_msb_n2:
	rrb rh0,#2
.org 0x3220
! sys_rrb_r_pattern_n1
test_sys_rrb_r_pattern_n1:
	rrb rh0,#1
.org 0x3240
! sys_rrb_r_pattern_n2
test_sys_rrb_r_pattern_n2:
	rrb rh0,#2
.org 0x3260
! sys_rlcb_r_one_n1_c0
test_sys_rlcb_r_one_n1_c0:
	rlcb rh0,#1
.org 0x3280
! sys_rlcb_r_one_n1_c1
test_sys_rlcb_r_one_n1_c1:
	rlcb rh0,#1
.org 0x32a0
! sys_rlcb_r_one_n2_c0
test_sys_rlcb_r_one_n2_c0:
	rlcb rh0,#2
.org 0x32c0
! sys_rlcb_r_one_n2_c1
test_sys_rlcb_r_one_n2_c1:
	rlcb rh0,#2
.org 0x32e0
! sys_rlcb_r_msb_n1_c0
test_sys_rlcb_r_msb_n1_c0:
	rlcb rh0,#1
.org 0x3300
! sys_rlcb_r_msb_n1_c1
test_sys_rlcb_r_msb_n1_c1:
	rlcb rh0,#1
.org 0x3320
! sys_rlcb_r_msb_n2_c0
test_sys_rlcb_r_msb_n2_c0:
	rlcb rh0,#2
.org 0x3340
! sys_rlcb_r_msb_n2_c1
test_sys_rlcb_r_msb_n2_c1:
	rlcb rh0,#2
.org 0x3360
! sys_rlcb_r_pattern_n1_c0
test_sys_rlcb_r_pattern_n1_c0:
	rlcb rh0,#1
.org 0x3380
! sys_rlcb_r_pattern_n1_c1
test_sys_rlcb_r_pattern_n1_c1:
	rlcb rh0,#1
.org 0x33a0
! sys_rlcb_r_pattern_n2_c0
test_sys_rlcb_r_pattern_n2_c0:
	rlcb rh0,#2
.org 0x33c0
! sys_rlcb_r_pattern_n2_c1
test_sys_rlcb_r_pattern_n2_c1:
	rlcb rh0,#2
.org 0x33e0
! sys_rrcb_r_one_n1_c0
test_sys_rrcb_r_one_n1_c0:
	rrcb rh0,#1
.org 0x3400
! sys_rrcb_r_one_n1_c1
test_sys_rrcb_r_one_n1_c1:
	rrcb rh0,#1
.org 0x3420
! sys_rrcb_r_one_n2_c0
test_sys_rrcb_r_one_n2_c0:
	rrcb rh0,#2
.org 0x3440
! sys_rrcb_r_one_n2_c1
test_sys_rrcb_r_one_n2_c1:
	rrcb rh0,#2
.org 0x3460
! sys_rrcb_r_msb_n1_c0
test_sys_rrcb_r_msb_n1_c0:
	rrcb rh0,#1
.org 0x3480
! sys_rrcb_r_msb_n1_c1
test_sys_rrcb_r_msb_n1_c1:
	rrcb rh0,#1
.org 0x34a0
! sys_rrcb_r_msb_n2_c0
test_sys_rrcb_r_msb_n2_c0:
	rrcb rh0,#2
.org 0x34c0
! sys_rrcb_r_msb_n2_c1
test_sys_rrcb_r_msb_n2_c1:
	rrcb rh0,#2
.org 0x34e0
! sys_rrcb_r_pattern_n1_c0
test_sys_rrcb_r_pattern_n1_c0:
	rrcb rh0,#1
.org 0x3500
! sys_rrcb_r_pattern_n1_c1
test_sys_rrcb_r_pattern_n1_c1:
	rrcb rh0,#1
.org 0x3520
! sys_rrcb_r_pattern_n2_c0
test_sys_rrcb_r_pattern_n2_c0:
	rrcb rh0,#2
.org 0x3540
! sys_rrcb_r_pattern_n2_c1
test_sys_rrcb_r_pattern_n2_c1:
	rrcb rh0,#2
.org 0x3560
! sys_rldb_bcd_00
test_sys_rldb_bcd_00:
	rldb rl0,rh1
.org 0x3580
! sys_rldb_bcd_99
test_sys_rldb_bcd_99:
	rldb rl0,rh1
.org 0x35a0
! sys_rldb_bcd_50
test_sys_rldb_bcd_50:
	rldb rl0,rh1
.org 0x35c0
! sys_rrdb_bcd_00
test_sys_rrdb_bcd_00:
	rrdb rl0,rh1
.org 0x35e0
! sys_rrdb_bcd_99
test_sys_rrdb_bcd_99:
	rrdb rl0,rh1
.org 0x3600
! sys_rrdb_bcd_50
test_sys_rrdb_bcd_50:
	rrdb rl0,rh1
.org 0x3620
! sys_bit_r_b0_zero
test_sys_bit_r_b0_zero:
	bit r0,#0
.org 0x3640
! sys_bit_r_b0_allones
test_sys_bit_r_b0_allones:
	bit r0,#0
.org 0x3660
! sys_bit_r_b7_zero
test_sys_bit_r_b7_zero:
	bit r0,#7
.org 0x3680
! sys_bit_r_b7_allones
test_sys_bit_r_b7_allones:
	bit r0,#7
.org 0x36a0
! sys_bit_r_b15_zero
test_sys_bit_r_b15_zero:
	bit r0,#15
.org 0x36c0
! sys_bit_r_b15_allones
test_sys_bit_r_b15_allones:
	bit r0,#15
.org 0x36e0
! sys_set_r_b0_zero
test_sys_set_r_b0_zero:
	set r0,#0
.org 0x3700
! sys_set_r_b0_allones
test_sys_set_r_b0_allones:
	set r0,#0
.org 0x3720
! sys_set_r_b7_zero
test_sys_set_r_b7_zero:
	set r0,#7
.org 0x3740
! sys_set_r_b7_allones
test_sys_set_r_b7_allones:
	set r0,#7
.org 0x3760
! sys_set_r_b15_zero
test_sys_set_r_b15_zero:
	set r0,#15
.org 0x3780
! sys_set_r_b15_allones
test_sys_set_r_b15_allones:
	set r0,#15
.org 0x37a0
! sys_res_r_b0_zero
test_sys_res_r_b0_zero:
	res r0,#0
.org 0x37c0
! sys_res_r_b0_allones
test_sys_res_r_b0_allones:
	res r0,#0
.org 0x37e0
! sys_res_r_b7_zero
test_sys_res_r_b7_zero:
	res r0,#7
.org 0x3800
! sys_res_r_b7_allones
test_sys_res_r_b7_allones:
	res r0,#7
.org 0x3820
! sys_res_r_b15_zero
test_sys_res_r_b15_zero:
	res r0,#15
.org 0x3840
! sys_res_r_b15_allones
test_sys_res_r_b15_allones:
	res r0,#15
.org 0x3860
! sys_bitb_r_b0_zero
test_sys_bitb_r_b0_zero:
	bitb rh0,#0
.org 0x3880
! sys_bitb_r_b0_allones
test_sys_bitb_r_b0_allones:
	bitb rh0,#0
.org 0x38a0
! sys_bitb_r_b3_zero
test_sys_bitb_r_b3_zero:
	bitb rh0,#3
.org 0x38c0
! sys_bitb_r_b3_allones
test_sys_bitb_r_b3_allones:
	bitb rh0,#3
.org 0x38e0
! sys_bitb_r_b7_zero
test_sys_bitb_r_b7_zero:
	bitb rh0,#7
.org 0x3900
! sys_bitb_r_b7_allones
test_sys_bitb_r_b7_allones:
	bitb rh0,#7
.org 0x3920
! sys_setb_r_b0_zero
test_sys_setb_r_b0_zero:
	setb rh0,#0
.org 0x3940
! sys_setb_r_b0_allones
test_sys_setb_r_b0_allones:
	setb rh0,#0
.org 0x3960
! sys_setb_r_b3_zero
test_sys_setb_r_b3_zero:
	setb rh0,#3
.org 0x3980
! sys_setb_r_b3_allones
test_sys_setb_r_b3_allones:
	setb rh0,#3
.org 0x39a0
! sys_setb_r_b7_zero
test_sys_setb_r_b7_zero:
	setb rh0,#7
.org 0x39c0
! sys_setb_r_b7_allones
test_sys_setb_r_b7_allones:
	setb rh0,#7
.org 0x39e0
! sys_resb_r_b0_zero
test_sys_resb_r_b0_zero:
	resb rh0,#0
.org 0x3a00
! sys_resb_r_b0_allones
test_sys_resb_r_b0_allones:
	resb rh0,#0
.org 0x3a20
! sys_resb_r_b3_zero
test_sys_resb_r_b3_zero:
	resb rh0,#3
.org 0x3a40
! sys_resb_r_b3_allones
test_sys_resb_r_b3_allones:
	resb rh0,#3
.org 0x3a60
! sys_resb_r_b7_zero
test_sys_resb_r_b7_zero:
	resb rh0,#7
.org 0x3a80
! sys_resb_r_b7_allones
test_sys_resb_r_b7_allones:
	resb rh0,#7
.org 0x3aa0
! sys_inc_r_n1_zero
test_sys_inc_r_n1_zero:
	inc r0,#1
.org 0x3ac0
! sys_inc_r_n1_one
test_sys_inc_r_n1_one:
	inc r0,#1
.org 0x3ae0
! sys_inc_r_n1_max
test_sys_inc_r_n1_max:
	inc r0,#1
.org 0x3b00
! sys_inc_r_n1_half
test_sys_inc_r_n1_half:
	inc r0,#1
.org 0x3b20
! sys_inc_r_n2_zero
test_sys_inc_r_n2_zero:
	inc r0,#2
.org 0x3b40
! sys_inc_r_n2_one
test_sys_inc_r_n2_one:
	inc r0,#2
.org 0x3b60
! sys_inc_r_n2_max
test_sys_inc_r_n2_max:
	inc r0,#2
.org 0x3b80
! sys_inc_r_n2_half
test_sys_inc_r_n2_half:
	inc r0,#2
.org 0x3ba0
! sys_inc_r_n16_zero
test_sys_inc_r_n16_zero:
	inc r0,#16
.org 0x3bc0
! sys_inc_r_n16_one
test_sys_inc_r_n16_one:
	inc r0,#16
.org 0x3be0
! sys_inc_r_n16_max
test_sys_inc_r_n16_max:
	inc r0,#16
.org 0x3c00
! sys_inc_r_n16_half
test_sys_inc_r_n16_half:
	inc r0,#16
.org 0x3c20
! sys_dec_r_n1_zero
test_sys_dec_r_n1_zero:
	dec r0,#1
.org 0x3c40
! sys_dec_r_n1_one
test_sys_dec_r_n1_one:
	dec r0,#1
.org 0x3c60
! sys_dec_r_n1_max
test_sys_dec_r_n1_max:
	dec r0,#1
.org 0x3c80
! sys_dec_r_n1_half
test_sys_dec_r_n1_half:
	dec r0,#1
.org 0x3ca0
! sys_dec_r_n2_zero
test_sys_dec_r_n2_zero:
	dec r0,#2
.org 0x3cc0
! sys_dec_r_n2_one
test_sys_dec_r_n2_one:
	dec r0,#2
.org 0x3ce0
! sys_dec_r_n2_max
test_sys_dec_r_n2_max:
	dec r0,#2
.org 0x3d00
! sys_dec_r_n2_half
test_sys_dec_r_n2_half:
	dec r0,#2
.org 0x3d20
! sys_dec_r_n16_zero
test_sys_dec_r_n16_zero:
	dec r0,#16
.org 0x3d40
! sys_dec_r_n16_one
test_sys_dec_r_n16_one:
	dec r0,#16
.org 0x3d60
! sys_dec_r_n16_max
test_sys_dec_r_n16_max:
	dec r0,#16
.org 0x3d80
! sys_dec_r_n16_half
test_sys_dec_r_n16_half:
	dec r0,#16
.org 0x3da0
! sys_incb_r_n1_zero
test_sys_incb_r_n1_zero:
	incb rh0,#1
.org 0x3dc0
! sys_incb_r_n1_one
test_sys_incb_r_n1_one:
	incb rh0,#1
.org 0x3de0
! sys_incb_r_n1_max
test_sys_incb_r_n1_max:
	incb rh0,#1
.org 0x3e00
! sys_incb_r_n1_half
test_sys_incb_r_n1_half:
	incb rh0,#1
.org 0x3e20
! sys_incb_r_n2_zero
test_sys_incb_r_n2_zero:
	incb rh0,#2
.org 0x3e40
! sys_incb_r_n2_one
test_sys_incb_r_n2_one:
	incb rh0,#2
.org 0x3e60
! sys_incb_r_n2_max
test_sys_incb_r_n2_max:
	incb rh0,#2
.org 0x3e80
! sys_incb_r_n2_half
test_sys_incb_r_n2_half:
	incb rh0,#2
.org 0x3ea0
! sys_incb_r_n16_zero
test_sys_incb_r_n16_zero:
	incb rh0,#16
.org 0x3ec0
! sys_incb_r_n16_one
test_sys_incb_r_n16_one:
	incb rh0,#16
.org 0x3ee0
! sys_incb_r_n16_max
test_sys_incb_r_n16_max:
	incb rh0,#16
.org 0x3f00
! sys_incb_r_n16_half
test_sys_incb_r_n16_half:
	incb rh0,#16
.org 0x3f20
! sys_decb_r_n1_zero
test_sys_decb_r_n1_zero:
	decb rh0,#1
.org 0x3f40
! sys_decb_r_n1_one
test_sys_decb_r_n1_one:
	decb rh0,#1
.org 0x3f60
! sys_decb_r_n1_max
test_sys_decb_r_n1_max:
	decb rh0,#1
.org 0x3f80
! sys_decb_r_n1_half
test_sys_decb_r_n1_half:
	decb rh0,#1
.org 0x3fa0
! sys_decb_r_n2_zero
test_sys_decb_r_n2_zero:
	decb rh0,#2
.org 0x3fc0
! sys_decb_r_n2_one
test_sys_decb_r_n2_one:
	decb rh0,#2
.org 0x3fe0
! sys_decb_r_n2_max
test_sys_decb_r_n2_max:
	decb rh0,#2
.org 0x4000
! sys_decb_r_n2_half
test_sys_decb_r_n2_half:
	decb rh0,#2
.org 0x4020
! sys_decb_r_n16_zero
test_sys_decb_r_n16_zero:
	decb rh0,#16
.org 0x4040
! sys_decb_r_n16_one
test_sys_decb_r_n16_one:
	decb rh0,#16
.org 0x4060
! sys_decb_r_n16_max
test_sys_decb_r_n16_max:
	decb rh0,#16
.org 0x4080
! sys_decb_r_n16_half
test_sys_decb_r_n16_half:
	decb rh0,#16
.org 0x40a0
! sys_inc_ir_n1_normal
test_sys_inc_ir_n1_normal:
	inc @r2,#1
.org 0x40c0
! sys_inc_ir_n1_max
test_sys_inc_ir_n1_max:
	inc @r2,#1
.org 0x40e0
! sys_inc_ir_n2_normal
test_sys_inc_ir_n2_normal:
	inc @r2,#2
.org 0x4100
! sys_inc_ir_n2_max
test_sys_inc_ir_n2_max:
	inc @r2,#2
.org 0x4120
! sys_dec_ir_n1_normal
test_sys_dec_ir_n1_normal:
	dec @r2,#1
.org 0x4140
! sys_dec_ir_n1_max
test_sys_dec_ir_n1_max:
	dec @r2,#1
.org 0x4160
! sys_dec_ir_n2_normal
test_sys_dec_ir_n2_normal:
	dec @r2,#2
.org 0x4180
! sys_dec_ir_n2_max
test_sys_dec_ir_n2_max:
	dec @r2,#2
.org 0x41a0
! sys_mult_rr_r_zero
test_sys_mult_rr_r_zero:
	mult rr0,r2
.org 0x41c0
! sys_mult_rr_r_one
test_sys_mult_rr_r_one:
	mult rr0,r2
.org 0x41e0
! sys_mult_rr_r_normal
test_sys_mult_rr_r_normal:
	mult rr0,r2
.org 0x4200
! sys_mult_rr_r_large
test_sys_mult_rr_r_large:
	mult rr0,r2
.org 0x4220
! sys_mult_rr_r_max
test_sys_mult_rr_r_max:
	mult rr0,r2
.org 0x4240
! sys_mult_rr_r_signed
test_sys_mult_rr_r_signed:
	mult rr0,r2
.org 0x4260
! sys_div_rr_r_normal
test_sys_div_rr_r_normal:
	div rr0,r2
.org 0x4280
! sys_div_rr_r_remainder
test_sys_div_rr_r_remainder:
	div rr0,r2
.org 0x42a0
! sys_div_rr_r_large
test_sys_div_rr_r_large:
	div rr0,r2
.org 0x42c0
! sys_div_rr_r_one
test_sys_div_rr_r_one:
	div rr0,r2
.org 0x42e0
! sys_multl_rq_rr_normal
test_sys_multl_rq_rr_normal:
	multl rq0,rr4
.org 0x4300
! sys_multl_rq_rr_large
test_sys_multl_rq_rr_large:
	multl rq0,rr4
.org 0x4320
! sys_divl_rq_rr_normal
test_sys_divl_rq_rr_normal:
	divl rq0,rr4
.org 0x4340
! sys_divl_rq_rr_large
test_sys_divl_rq_rr_large:
	divl rq0,rr4
.org 0x4360
! sys_dab_add_no_adj
test_sys_dab_add_no_adj:
	dab rh0
.org 0x4380
! sys_dab_add_low_adj
test_sys_dab_add_low_adj:
	dab rh0
.org 0x43a0
! sys_dab_add_high_adj
test_sys_dab_add_high_adj:
	dab rh0
.org 0x43c0
! sys_dab_add_both_adj
test_sys_dab_add_both_adj:
	dab rh0
.org 0x43e0
! sys_dab_sub_no_adj
test_sys_dab_sub_no_adj:
	dab rh0
.org 0x4400
! sys_dab_sub_adj
test_sys_dab_sub_adj:
	dab rh0
.org 0x4420
! sys_extsb_r_zero
test_sys_extsb_r_zero:
	extsb r0
.org 0x4440
! sys_extsb_r_pos
test_sys_extsb_r_pos:
	extsb r0
.org 0x4460
! sys_extsb_r_neg
test_sys_extsb_r_neg:
	extsb r0
.org 0x4480
! sys_exts_rr_zero
test_sys_exts_rr_zero:
	exts rr0
.org 0x44a0
! sys_exts_rr_pos
test_sys_exts_rr_pos:
	exts rr0
.org 0x44c0
! sys_exts_rr_neg
test_sys_exts_rr_neg:
	exts rr0
.org 0x44e0
! sys_extsl_rq_zero
test_sys_extsl_rq_zero:
	extsl rq0
.org 0x4500
! sys_extsl_rq_pos
test_sys_extsl_rq_pos:
	extsl rq0
.org 0x4520
! sys_extsl_rq_neg
test_sys_extsl_rq_neg:
	extsl rq0
.org 0x4540
! sys_setflg_m1
test_sys_setflg_m1:
	setflg p
.org 0x4560
! sys_setflg_m2
test_sys_setflg_m2:
	setflg s
.org 0x4580
! sys_setflg_m3
test_sys_setflg_m3:
	setflg s,p
.org 0x45a0
! sys_setflg_m4
test_sys_setflg_m4:
	setflg z
.org 0x45c0
! sys_setflg_m5
test_sys_setflg_m5:
	setflg z,p
.org 0x45e0
! sys_setflg_m6
test_sys_setflg_m6:
	setflg z,s
.org 0x4600
! sys_setflg_m7
test_sys_setflg_m7:
	setflg z,s,p
.org 0x4620
! sys_setflg_m8
test_sys_setflg_m8:
	setflg c
.org 0x4640
! sys_setflg_m9
test_sys_setflg_m9:
	setflg c,p
.org 0x4660
! sys_setflg_ma
test_sys_setflg_ma:
	setflg c,s
.org 0x4680
! sys_setflg_mb
test_sys_setflg_mb:
	setflg c,s,p
.org 0x46a0
! sys_setflg_mc
test_sys_setflg_mc:
	setflg c,z
.org 0x46c0
! sys_setflg_md
test_sys_setflg_md:
	setflg c,z,p
.org 0x46e0
! sys_setflg_me
test_sys_setflg_me:
	setflg c,z,s
.org 0x4700
! sys_setflg_mf
test_sys_setflg_mf:
	setflg c,z,s,p
.org 0x4720
! sys_resflg_m1
test_sys_resflg_m1:
	resflg p
.org 0x4740
! sys_resflg_m2
test_sys_resflg_m2:
	resflg s
.org 0x4760
! sys_resflg_m3
test_sys_resflg_m3:
	resflg s,p
.org 0x4780
! sys_resflg_m4
test_sys_resflg_m4:
	resflg z
.org 0x47a0
! sys_resflg_m5
test_sys_resflg_m5:
	resflg z,p
.org 0x47c0
! sys_resflg_m6
test_sys_resflg_m6:
	resflg z,s
.org 0x47e0
! sys_resflg_m7
test_sys_resflg_m7:
	resflg z,s,p
.org 0x4800
! sys_resflg_m8
test_sys_resflg_m8:
	resflg c
.org 0x4820
! sys_resflg_m9
test_sys_resflg_m9:
	resflg c,p
.org 0x4840
! sys_resflg_ma
test_sys_resflg_ma:
	resflg c,s
.org 0x4860
! sys_resflg_mb
test_sys_resflg_mb:
	resflg c,s,p
.org 0x4880
! sys_resflg_mc
test_sys_resflg_mc:
	resflg c,z
.org 0x48a0
! sys_resflg_md
test_sys_resflg_md:
	resflg c,z,p
.org 0x48c0
! sys_resflg_me
test_sys_resflg_me:
	resflg c,z,s
.org 0x48e0
! sys_resflg_mf
test_sys_resflg_mf:
	resflg c,z,s,p
.org 0x4900
! sys_comflg_m1
test_sys_comflg_m1:
	comflg p
.org 0x4920
! sys_comflg_m2
test_sys_comflg_m2:
	comflg s
.org 0x4940
! sys_comflg_m3
test_sys_comflg_m3:
	comflg s,p
.org 0x4960
! sys_comflg_m4
test_sys_comflg_m4:
	comflg z
.org 0x4980
! sys_comflg_m5
test_sys_comflg_m5:
	comflg z,p
.org 0x49a0
! sys_comflg_m6
test_sys_comflg_m6:
	comflg z,s
.org 0x49c0
! sys_comflg_m7
test_sys_comflg_m7:
	comflg z,s,p
.org 0x49e0
! sys_comflg_m8
test_sys_comflg_m8:
	comflg c
.org 0x4a00
! sys_comflg_m9
test_sys_comflg_m9:
	comflg c,p
.org 0x4a20
! sys_comflg_ma
test_sys_comflg_ma:
	comflg c,s
.org 0x4a40
! sys_comflg_mb
test_sys_comflg_mb:
	comflg c,s,p
.org 0x4a60
! sys_comflg_mc
test_sys_comflg_mc:
	comflg c,z
.org 0x4a80
! sys_comflg_md
test_sys_comflg_md:
	comflg c,z,p
.org 0x4aa0
! sys_comflg_me
test_sys_comflg_me:
	comflg c,z,s
.org 0x4ac0
! sys_comflg_mf
test_sys_comflg_mf:
	comflg c,z,s,p
.org 0x4ae0
! sys_tcc_f_true
test_sys_tcc_f_true:
	tcc f,r0
.org 0x4b00
! sys_tcc_f_false
test_sys_tcc_f_false:
	tcc f,r0
.org 0x4b20
! sys_tccb_f_true
test_sys_tccb_f_true:
	tccb f,rh0
.org 0x4b40
! sys_tccb_f_false
test_sys_tccb_f_false:
	tccb f,rh0
.org 0x4b60
! sys_tcc_lt_true
test_sys_tcc_lt_true:
	tcc lt,r0
.org 0x4b80
! sys_tcc_lt_false
test_sys_tcc_lt_false:
	tcc lt,r0
.org 0x4ba0
! sys_tccb_lt_true
test_sys_tccb_lt_true:
	tccb lt,rh0
.org 0x4bc0
! sys_tccb_lt_false
test_sys_tccb_lt_false:
	tccb lt,rh0
.org 0x4be0
! sys_tcc_le_true
test_sys_tcc_le_true:
	tcc le,r0
.org 0x4c00
! sys_tcc_le_false
test_sys_tcc_le_false:
	tcc le,r0
.org 0x4c20
! sys_tccb_le_true
test_sys_tccb_le_true:
	tccb le,rh0
.org 0x4c40
! sys_tccb_le_false
test_sys_tccb_le_false:
	tccb le,rh0
.org 0x4c60
! sys_tcc_ule_true
test_sys_tcc_ule_true:
	tcc ule,r0
.org 0x4c80
! sys_tcc_ule_false
test_sys_tcc_ule_false:
	tcc ule,r0
.org 0x4ca0
! sys_tccb_ule_true
test_sys_tccb_ule_true:
	tccb ule,rh0
.org 0x4cc0
! sys_tccb_ule_false
test_sys_tccb_ule_false:
	tccb ule,rh0
.org 0x4ce0
! sys_tcc_ov_true
test_sys_tcc_ov_true:
	tcc ov,r0
.org 0x4d00
! sys_tcc_ov_false
test_sys_tcc_ov_false:
	tcc ov,r0
.org 0x4d20
! sys_tccb_ov_true
test_sys_tccb_ov_true:
	tccb ov,rh0
.org 0x4d40
! sys_tccb_ov_false
test_sys_tccb_ov_false:
	tccb ov,rh0
.org 0x4d60
! sys_tcc_mi_true
test_sys_tcc_mi_true:
	tcc mi,r0
.org 0x4d80
! sys_tcc_mi_false
test_sys_tcc_mi_false:
	tcc mi,r0
.org 0x4da0
! sys_tccb_mi_true
test_sys_tccb_mi_true:
	tccb mi,rh0
.org 0x4dc0
! sys_tccb_mi_false
test_sys_tccb_mi_false:
	tccb mi,rh0
.org 0x4de0
! sys_tcc_eq_true
test_sys_tcc_eq_true:
	tcc eq,r0
.org 0x4e00
! sys_tcc_eq_false
test_sys_tcc_eq_false:
	tcc eq,r0
.org 0x4e20
! sys_tccb_eq_true
test_sys_tccb_eq_true:
	tccb eq,rh0
.org 0x4e40
! sys_tccb_eq_false
test_sys_tccb_eq_false:
	tccb eq,rh0
.org 0x4e60
! sys_tcc_c_true
test_sys_tcc_c_true:
	tcc c,r0
.org 0x4e80
! sys_tcc_c_false
test_sys_tcc_c_false:
	tcc c,r0
.org 0x4ea0
! sys_tccb_c_true
test_sys_tccb_c_true:
	tccb c,rh0
.org 0x4ec0
! sys_tccb_c_false
test_sys_tccb_c_false:
	tccb c,rh0
.org 0x4ee0
! sys_tcc_t_true
test_sys_tcc_t_true:
	tcc t,r0
.org 0x4f00
! sys_tcc_t_false
test_sys_tcc_t_false:
	tcc t,r0
.org 0x4f20
! sys_tccb_t_true
test_sys_tccb_t_true:
	tccb t,rh0
.org 0x4f40
! sys_tccb_t_false
test_sys_tccb_t_false:
	tccb t,rh0
.org 0x4f60
! sys_tcc_ge_true
test_sys_tcc_ge_true:
	tcc ge,r0
.org 0x4f80
! sys_tcc_ge_false
test_sys_tcc_ge_false:
	tcc ge,r0
.org 0x4fa0
! sys_tccb_ge_true
test_sys_tccb_ge_true:
	tccb ge,rh0
.org 0x4fc0
! sys_tccb_ge_false
test_sys_tccb_ge_false:
	tccb ge,rh0
.org 0x4fe0
! sys_tcc_gt_true
test_sys_tcc_gt_true:
	tcc gt,r0
.org 0x5000
! sys_tcc_gt_false
test_sys_tcc_gt_false:
	tcc gt,r0
.org 0x5020
! sys_tccb_gt_true
test_sys_tccb_gt_true:
	tccb gt,rh0
.org 0x5040
! sys_tccb_gt_false
test_sys_tccb_gt_false:
	tccb gt,rh0
.org 0x5060
! sys_tcc_ugt_true
test_sys_tcc_ugt_true:
	tcc ugt,r0
.org 0x5080
! sys_tcc_ugt_false
test_sys_tcc_ugt_false:
	tcc ugt,r0
.org 0x50a0
! sys_tccb_ugt_true
test_sys_tccb_ugt_true:
	tccb ugt,rh0
.org 0x50c0
! sys_tccb_ugt_false
test_sys_tccb_ugt_false:
	tccb ugt,rh0
.org 0x50e0
! sys_tcc_nov_true
test_sys_tcc_nov_true:
	tcc nov,r0
.org 0x5100
! sys_tcc_nov_false
test_sys_tcc_nov_false:
	tcc nov,r0
.org 0x5120
! sys_tccb_nov_true
test_sys_tccb_nov_true:
	tccb nov,rh0
.org 0x5140
! sys_tccb_nov_false
test_sys_tccb_nov_false:
	tccb nov,rh0
.org 0x5160
! sys_tcc_pl_true
test_sys_tcc_pl_true:
	tcc pl,r0
.org 0x5180
! sys_tcc_pl_false
test_sys_tcc_pl_false:
	tcc pl,r0
.org 0x51a0
! sys_tccb_pl_true
test_sys_tccb_pl_true:
	tccb pl,rh0
.org 0x51c0
! sys_tccb_pl_false
test_sys_tccb_pl_false:
	tccb pl,rh0
.org 0x51e0
! sys_tcc_ne_true
test_sys_tcc_ne_true:
	tcc ne,r0
.org 0x5200
! sys_tcc_ne_false
test_sys_tcc_ne_false:
	tcc ne,r0
.org 0x5220
! sys_tccb_ne_true
test_sys_tccb_ne_true:
	tccb ne,rh0
.org 0x5240
! sys_tccb_ne_false
test_sys_tccb_ne_false:
	tccb ne,rh0
.org 0x5260
! sys_tcc_nc_true
test_sys_tcc_nc_true:
	tcc nc,r0
.org 0x5280
! sys_tcc_nc_false
test_sys_tcc_nc_false:
	tcc nc,r0
.org 0x52a0
! sys_tccb_nc_true
test_sys_tccb_nc_true:
	tccb nc,rh0
.org 0x52c0
! sys_tccb_nc_false
test_sys_tccb_nc_false:
	tccb nc,rh0
.org 0x52e0
! sys_ld_r_r_normal
test_sys_ld_r_r_normal:
	ld r0,r1
.org 0x5300
! sys_ld_r_r_zero
test_sys_ld_r_r_zero:
	ld r0,r1
.org 0x5320
! sys_ld_r_r_max
test_sys_ld_r_r_max:
	ld r0,r1
.org 0x5340
! sys_ld_r_im_normal
test_sys_ld_r_im_normal:
	ld r0,#0x1234
.org 0x5360
! sys_ld_r_im_zero
test_sys_ld_r_im_zero:
	ld r0,#0x0000
.org 0x5380
! sys_ld_r_im_max
test_sys_ld_r_im_max:
	ld r0,#0xffff
.org 0x53a0
! sys_ld_r_ir_normal
test_sys_ld_r_ir_normal:
	ld r0,@r2
.org 0x53c0
! sys_ld_r_ir_zero
test_sys_ld_r_ir_zero:
	ld r0,@r2
.org 0x53e0
! sys_ld_r_da_normal
test_sys_ld_r_da_normal:
	ld r0,0x0400
.org 0x5400
! sys_ld_r_da_zero
test_sys_ld_r_da_zero:
	ld r0,0x0400
.org 0x5420
! sys_ld_da_r_normal
test_sys_ld_da_r_normal:
	ld 0x0400,r0
.org 0x5440
! sys_ld_da_r_zero
test_sys_ld_da_r_zero:
	ld 0x0400,r0
.org 0x5460
! sys_ld_r_x_basic
test_sys_ld_r_x_basic:
	ld r0,0x0400(r2)
.org 0x5480
! sys_ld_ir_r_basic
test_sys_ld_ir_r_basic:
	ld @r2,r0
.org 0x54a0
! sys_ldb_r_r_normal
test_sys_ldb_r_r_normal:
	ldb rh0,rh1
.org 0x54c0
! sys_ldb_r_r_zero
test_sys_ldb_r_r_zero:
	ldb rh0,rh1
.org 0x54e0
! sys_ldb_r_im_normal
test_sys_ldb_r_im_normal:
	ldb rh0,#0x42
.org 0x5500
! sys_ldb_r_im_max
test_sys_ldb_r_im_max:
	ldb rh0,#0xff
.org 0x5520
! sys_ldl_rr_rr_normal
test_sys_ldl_rr_rr_normal:
	ldl rr0,rr2
.org 0x5540
! sys_ldl_rr_rr_zero
test_sys_ldl_rr_rr_zero:
	ldl rr0,rr2
.org 0x5560
! sys_ldl_rr_ir_basic
test_sys_ldl_rr_ir_basic:
	ldl rr0,@r2
.org 0x5580
! sys_ldk_r_n0
test_sys_ldk_r_n0:
	ldk r0,#0
.org 0x55a0
! sys_ldk_r_n5
test_sys_ldk_r_n5:
	ldk r0,#5
.org 0x55c0
! sys_ldk_r_n15
test_sys_ldk_r_n15:
	ldk r0,#15
.org 0x55e0
! sys_ldm_load_3
test_sys_ldm_load_3:
	ldm r3,@r2,#3
.org 0x5600
! sys_ldm_store_3
test_sys_ldm_store_3:
	ldm @r2,r3,#3
.org 0x5620
! sys_ex_r_r_normal
test_sys_ex_r_r_normal:
	ex r0,r1
.org 0x5640
! sys_ex_r_r_same
test_sys_ex_r_r_same:
	ex r0,r1
.org 0x5660
! sys_exb_r_r_normal
test_sys_exb_r_r_normal:
	exb rh0,rh1
.org 0x5680
! sys_exb_r_r_same
test_sys_exb_r_r_same:
	exb rh0,rh1
.org 0x56a0
! sys_push_r_normal
test_sys_push_r_normal:
	push @r15,r0
.org 0x56c0
! sys_push_r_max
test_sys_push_r_max:
	push @r15,r0
.org 0x56e0
! sys_pop_r_normal
test_sys_pop_r_normal:
	pop r0,@r15
.org 0x5700
! sys_pop_r_zero
test_sys_pop_r_zero:
	pop r0,@r15
.org 0x5720
! sys_pushl_rr_normal
test_sys_pushl_rr_normal:
	pushl @r15,rr0
.org 0x5740
! sys_pushl_rr_zero
test_sys_pushl_rr_zero:
	pushl @r15,rr0
.org 0x5760
! sys_popl_rr_normal
test_sys_popl_rr_normal:
	popl rr0,@r15
.org 0x5780
! sys_popl_rr_zero
test_sys_popl_rr_zero:
	popl rr0,@r15
.org 0x57a0
! sys_ldi_single
test_sys_ldi_single:
	ldi @r3,@r1,r2
.org 0x57c0
! sys_ldi_last
test_sys_ldi_last:
	ldi @r3,@r1,r2
.org 0x57e0
! sys_ldir_3words
test_sys_ldir_3words:
	ldir @r3,@r1,r2
.org 0x5800
! sys_ldir_1word
test_sys_ldir_1word:
	ldir @r3,@r1,r2
.org 0x5820
! sys_ldd_single
test_sys_ldd_single:
	ldd @r3,@r1,r2
.org 0x5840
! sys_ldd_last
test_sys_ldd_last:
	ldd @r3,@r1,r2
.org 0x5860
! sys_lddr_3words
test_sys_lddr_3words:
	lddr @r3,@r1,r2
.org 0x5880
! sys_lddr_1word
test_sys_lddr_1word:
	lddr @r3,@r1,r2
.org 0x58a0
! sys_ldib_single
test_sys_ldib_single:
	ldib @r3,@r1,r2
.org 0x58c0
! sys_ldirb_3bytes
test_sys_ldirb_3bytes:
	ldirb @r3,@r1,r2
.org 0x58e0
! sys_lddb_single
test_sys_lddb_single:
	lddb @r3,@r1,r2
.org 0x5900
! sys_lddrb_3bytes
test_sys_lddrb_3bytes:
	lddrb @r3,@r1,r2
.org 0x5920
! sys_cpi_match
test_sys_cpi_match:
	cpi r0,@r1,r2,eq
.org 0x5940
! sys_cpi_no_match
test_sys_cpi_no_match:
	cpi r0,@r1,r2,eq
.org 0x5960
! sys_cpir_match_mid
test_sys_cpir_match_mid:
	cpir r0,@r1,r2,eq
.org 0x5980
! sys_cpir_no_match
test_sys_cpir_no_match:
	cpir r0,@r1,r2,eq
.org 0x59a0
! sys_cpd_match
test_sys_cpd_match:
	cpd r0,@r1,r2,eq
.org 0x59c0
! sys_cpd_no_match
test_sys_cpd_no_match:
	cpd r0,@r1,r2,eq
.org 0x59e0
! sys_cpdr_match
test_sys_cpdr_match:
	cpdr r0,@r1,r2,eq
.org 0x5a00
! sys_cpdr_no_match
test_sys_cpdr_no_match:
	cpdr r0,@r1,r2,eq
.org 0x5a20
! sys_cpib_match
test_sys_cpib_match:
	cpib rh0,@r1,r2,eq
.org 0x5a40
! sys_cpib_no_match
test_sys_cpib_no_match:
	cpib rh0,@r1,r2,eq
.org 0x5a60
! sys_cpirb_match
test_sys_cpirb_match:
	cpirb rh0,@r1,r2,eq
.org 0x5a80
! sys_cpirb_no_match
test_sys_cpirb_no_match:
	cpirb rh0,@r1,r2,eq
.org 0x5aa0
! sys_cpdb_match
test_sys_cpdb_match:
	cpdb rh0,@r1,r2,eq
.org 0x5ac0
! sys_cpdrb_no_match
test_sys_cpdrb_no_match:
	cpdrb rh0,@r1,r2,eq
.org 0x5ae0
! sys_cpsi_match
test_sys_cpsi_match:
	cpsi @r3,@r1,r2,eq
.org 0x5b00
! sys_cpsi_no_match
test_sys_cpsi_no_match:
	cpsi @r3,@r1,r2,eq
.org 0x5b20
! sys_cpsib_match
test_sys_cpsib_match:
	cpsib @r3,@r1,r2,eq
.org 0x5b40
! sys_cpsib_no_match
test_sys_cpsib_no_match:
	cpsib @r3,@r1,r2,eq
.org 0x5b60
! sys_cpsir_match
test_sys_cpsir_match:
	cpsir @r3,@r1,r2,eq
.org 0x5b80
! sys_cpsir_no_match
test_sys_cpsir_no_match:
	cpsir @r3,@r1,r2,eq
.org 0x5ba0
! sys_cpsirb_match
test_sys_cpsirb_match:
	cpsirb @r3,@r1,r2,eq
.org 0x5bc0
! sys_cpsirb_no_match
test_sys_cpsirb_no_match:
	cpsirb @r3,@r1,r2,eq
.org 0x5be0
! sys_cpsd_match
test_sys_cpsd_match:
	cpsd @r3,@r1,r2,eq
.org 0x5c00
! sys_cpsd_no_match
test_sys_cpsd_no_match:
	cpsd @r3,@r1,r2,eq
.org 0x5c20
! sys_cpsdb_match
test_sys_cpsdb_match:
	cpsdb @r3,@r1,r2,eq
.org 0x5c40
! sys_cpsdb_no_match
test_sys_cpsdb_no_match:
	cpsdb @r3,@r1,r2,eq
.org 0x5c60
! sys_cpsdr_match
test_sys_cpsdr_match:
	cpsdr @r3,@r1,r2,eq
.org 0x5c80
! sys_cpsdr_no_match
test_sys_cpsdr_no_match:
	cpsdr @r3,@r1,r2,eq
.org 0x5ca0
! sys_cpsdrb_match
test_sys_cpsdrb_match:
	cpsdrb @r3,@r1,r2,eq
.org 0x5cc0
! sys_cpsdrb_no_match
test_sys_cpsdrb_no_match:
	cpsdrb @r3,@r1,r2,eq
.org 0x5ce0
! sys_trib_basic
test_sys_trib_basic:
	trib @r3,@r1,r2
.org 0x5d00
! sys_trib_zero
test_sys_trib_zero:
	trib @r3,@r1,r2
.org 0x5d20
! sys_trirb_basic
test_sys_trirb_basic:
	trirb @r3,@r1,r2
.org 0x5d40
! sys_trirb_zero
test_sys_trirb_zero:
	trirb @r3,@r1,r2
.org 0x5d60
! sys_trdb_basic
test_sys_trdb_basic:
	trdb @r3,@r1,r2
.org 0x5d80
! sys_trdb_zero
test_sys_trdb_zero:
	trdb @r3,@r1,r2
.org 0x5da0
! sys_trdrb_basic
test_sys_trdrb_basic:
	trdrb @r3,@r1,r2
.org 0x5dc0
! sys_trdrb_zero
test_sys_trdrb_zero:
	trdrb @r3,@r1,r2
.org 0x5de0
! sys_trtib_basic
test_sys_trtib_basic:
	trtib @r3,@r1,r2
.org 0x5e00
! sys_trtib_zero
test_sys_trtib_zero:
	trtib @r3,@r1,r2
.org 0x5e20
! sys_trtdb_basic
test_sys_trtdb_basic:
	trtdb @r3,@r1,r2
.org 0x5e40
! sys_trtdb_zero
test_sys_trtdb_zero:
	trtdb @r3,@r1,r2
.org 0x5e60
! sys_lda_r_da_operand
test_sys_lda_r_da_operand:
	lda r0,0x0400
.org 0x5e80
! sys_lda_r_da_src
test_sys_lda_r_da_src:
	lda r0,0x0600
.org 0x5ea0
! sys_ldctl_read_fcw
test_sys_ldctl_read_fcw:
	ldctl r0,fcw
.org 0x5ec0
! sys_ldctl_write_fcw
test_sys_ldctl_write_fcw:
	ldctl fcw,r0
.org 0x5ee0
! sys_ldctlb_read_flags
test_sys_ldctlb_read_flags:
	ldctlb rh0,flags
.org 0x5f00
! sys_ldctlb_write_flags
test_sys_ldctlb_write_flags:
	ldctlb flags,rh0
