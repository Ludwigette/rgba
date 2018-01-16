# arm_gen.py --- 
# 
# Filename: arm_gen.py
# Author: Louise <louise>
# Created: Sat Jan 13 17:25:38 2018 (+0100)
# Last-Updated: Tue Jan 16 20:11:07 2018 (+0100)
#           By: Louise <louise>
# 

def write_branch(high, low):
    link = (high & 0x10) != 0
    print("\tlet offset = ((instr << 8) as i32) >> 6;")
    print("\tlet old_pc = _cpu.get_register(15);")
    
    if link:
        print("\t_cpu.set_register(14, old_pc - 4);")

    print("\tlet new_pc = ((old_pc as i32) + offset) as u32;")
    print("\t_cpu.set_register(15, new_pc);")
    print("\t_cpu.advance_pipeline(_io);")

def write_branch_exchange():
    print("\tlet dest = _cpu.get_register((instr & 0xF) as usize);")
    print("\tif dest & 1 != 0 { _cpu.state = CpuState::Thumb; }")
    print("\t_cpu.registers[15] = dest & 0xFFFFFFFE;")
    print("\t_cpu.advance_pipeline(_io);")
    
def write_op2_imm(high, low):
    s = (high & 0x01) != 0
    
    print("\tlet imm = instr & 0xFF;")
    print("\tlet rot = (instr & 0xF00) >> 7;")
    print("\tlet op2 = imm.rotate_right(rot);")
    if s:
        print("\tif rot != 0 { _cpu.carry = (op2 >> 31) != 0; }")

def write_op2_reg(low, s):
    shift = (low & 0x6) >> 2
    
    print("\tlet rm = _cpu.get_register((instr & 0xF) as usize);")
    if (low & 1) == 0: # By immediate
        print("\tlet amount = (instr >> 7) & 0x1f;")
        if shift == 0:
            print("\tlet op2 = if amount == 0 { rm } else {", end = "")
            if s: print(" let tmp = rm << (amount - 1); _cpu.carry = (tmp >> 31) != 0; tmp << 1 };")
            else: print(" rm << amount };")
        elif shift == 1:
            print("\tlet op2 = if amount == 0 { ", end = "")
            if s:
                print("_cpu.carry = (rm & 0x80000000) != 0; 0 } else { let tmp = rm >> (amount - 1); ",end="")
                print("_cpu.carry = (tmp & 1) != 0; tmp >> 1 };")
            else:
                print("0 } else { rm >> amount };")
        elif shift == 2:
            print("\tlet op2 = if amount == 0 { ", end = "")
            if s:
                print("_cpu.carry = (rm & 0x80000000) != 0; ((rm as i32) >> 31) as u32 } else { ", end="")
                print("let tmp = ((rm as i32) >> (amount - 1)) as u32; _cpu.carry = tmp & 1 != 0; ", end="")
                print("((tmp as i32) >> 1) as u32 };")
            else:
                print("((rm as i32) >> 31 } else { ((rm as i32) >> amount) as u32 };")
        elif shift == 3:
            print("\tlet op2 = if amount == 0 { ", end="")
            if s:
                print("let tmp = (rm >> 1) | ((_cpu.carry as u32) << 31);  _cpu.carry = (rm & 1) != 0; ")
                print("tmp } else { let tmp = rm.rotate_right(amount); _cpu.carry = (tmp >> 31) != 0; ")
                print("tmp };")
            else:
                print("(rm >> 1) | ((_cpu.carry as u32) << 31) } else { rm.rotate_right(amount) };")
        
    else: # By register
        print("\tlet amount = _cpu.get_register(((instr >> 8) & 0xF) as usize) & 0xFF;")
        if shift == 0:
            if s:
                print("\tlet tmp = rm << (amount - 1); _cpu.carry = (tmp >> 31) != 0;")
                print("\tlet op2 = tmp << 1;")
            else:
                print("\tlet op2 = rm << amount;")
        elif shift == 1:
            if s:
                print("\tlet tmp = rm >> (amount - 1); _cpu.carry = (tmp & 1) != 0;")
                print("\tlet op2 = tmp >> 1 ;")
            else:
                print("\tlet op2 = rm >> amount;")
        elif shift == 2:
            if s:
                print("\tlet tmp = ((rm as i32) >> (amount - 1)) as u32; _cpu.carry = tmp & 1 != 0;")
                print("\tlet op2 = ((tmp as i32) >> 1) as u32;")
            else:
                print("\tlet op2 = ((rm as i32) >> amount) as u32;")
        elif shift == 3:
            print("\tlet op2 = rm.rotate_right(amount);")
            if s:
                print("\t_cpu.carry = (op2 >> 31) != 0;")
    
    
def write_alu(high, low):
    op = (high & 0x1e) >> 1
    s = (high & 0x01) != 0
    imm = (high & 0x20) != 0

    if op == 5 or op == 6 or op == 7:
        print("\tlet cf = _cpu.carry;")
    
    # Generation op2 code
    if imm:
        write_op2_imm(high, low)
    else:
        write_op2_reg(low, s)
        
    test = (op & 0xc == 0x8)
        
    if (op & 0xc == 0x8) and not s:
        print("\tpanic!(\"Generating bad ALU instruction ({:08x}))\", instr);")
        return
    
    if op != 13 and op != 15:
        print("\tlet rn = _cpu.get_register(((instr >> 16) & 0xF) as usize);")

    if not test or s:
        print("\tlet rd = (instr >> 12) & 0xF;")
    
    if op == 8 or op == 0: # AND, TST
        print("\tlet res = rn & op2;")
    elif op == 9 or op == 1: # EOR, TEQ
        print("\tlet res = rn | op2;");
    elif op == 10 or op == 2: # SUB, CMP
        print("\tlet res = rn.wrapping_sub(op2);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = rn >= op2;")
            print("\t\t_cpu.overflow = (rn ^ op2) & (rn ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 3: # RSB
        print("\tlet res = op2.wrapping_sub(rn);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = op2 >= rn;")
            print("\t\t_cpu.overflow = (rn ^ op2) & (op2 ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 11 or op == 4: # ADD, CMN
        print("\tlet res = rn.wrapping_add(op2);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = rn > res;")
            print("\t\t_cpu.overflow = !(rn ^ op2) & (rn ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 5: # ADC
        print("\tlet res = rn.wrapping_add(op2).wrapping_add(cf as u32);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = if cf { rn >= res } else { rn > res };")
            print("\t\t_cpu.overflow = !(rn ^ op2) & (rn ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 6: # SBC
        print("\tlet res = rn.wrapping_sub(op2).wrapping_sub(cf as u32);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = if cf { rn > op2 } else { rn >= op2 };")
            print("\t\t_cpu.overflow = (rn ^ op2) & (rn ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 7: # RSC
        print("\tlet res = op2.wrapping_sub(rn).wrapping_sub(cf as u32);")
        if s:
            print("\tif rd != 15 {")
            print("\t\t_cpu.carry = if cf { op2 > rn } else { op2 >= rn };")
            print("\t\t_cpu.overflow = (rn ^ op2) & (op2 ^ res) & 0x80000000 != 0;")
            print("\t}")
    elif op == 12: # ORR
        print("\tlet res = rn | op2;")
    elif op == 13: # MOV
        print("\tlet res = op2;")
    elif op == 14: # BIC
        print("\tlet res = rn & !op2;");
    elif op == 15: # MVN
        print("\tlet res = !op2;");
    else:
        print("\tlet res = 0;")
        print("\tunimplemented!(\"ALU instruction not implemented : {:08x}\", instr);")

    if s:
        print("\tif rd != 15 { _cpu.sign = (res as i32) < 0; _cpu.zero = res == 0; }")
    if not test:
        print("\t_cpu.set_register(rd as usize, res);")
        print("\tif rd == 15 { unimplemented!(\"Setting r15 via ALU\"); }")

def write_psr(high, low):
    reg = "cpsr" if (high & 0x04 == 0) else "spsr"
    
    if high & 0x02 == 0x02:
        if high & 0x20 != 0: # Immediate value
            print("\tlet val = (instr & 0xFF).rotate_right((instr & 0xF00) >> 7);")
        else: # Register
            print("\tlet val = _cpu.get_register((instr & 0xF) as usize);")

        print("\tif instr & 0x000F0000 == 0x00080000 { _cpu.set_%s_flg(val); } else { _cpu.set_%s(val); }"
              % (reg, reg))
    else:
        print("\tlet val = _cpu.%s();" % reg)
        print("\tlet rd = (instr & 0xF000) >> 12;")
        print("\t_cpu.set_register(rd as usize, val);")
        
def write_sdt(high, low):
    pre = high & 0x10 != 0
    
    print("\tlet rd = (instr >> 12) & 0xF;")
    print("\tif rd == 15 { unimplemented!(\"Writing to r15\"); }")
    print("\tlet rn = _cpu.get_register(((instr >> 16) & 0xF) as usize);")
    
    if high & 0x20 == 0:
        print("\tlet off = instr & 0xFFF;")
    else:
        write_op2_reg(low, False)
        print("\tlet off = op2;")

    if pre:
        if high & 0x08 != 0:
            print("\tlet addr = rn.wrapping_add(off);")
        else:
            print("\tlet addr = rn.wrapping_sub(off);")
    else:
        print("\tlet addr = rn;")
        
    if high & 0x01 == 0:
        print("\tlet val = _cpu.get_register(rd as usize);")
        if high & 0x04 != 0: # Byte quantity
            print("\t_cpu.write_u8(_io, addr as usize, val as u8);")
        else: # Word quantity
            print("\t_cpu.write_u32(_io, addr as usize, val);")
    else:
        if high & 0x04 != 0: # Byte quantity
            print("\tlet res = _cpu.read_u8(_io, addr as usize) as u32;")
        else: # Word quantity
            print("\tlet res = if addr & 3 != 0 { ")
            print("\t\tlet rot = (addr & 3) << 3; _cpu.read_u32(_io, (addr & !3) as usize).rotate_right(rot)")
            print("\t} else {")
            print("\t\t_cpu.read_u32(_io, addr as usize)")
            print("\t};")
        print("_cpu.set_register(rd as usize, res);")

    if not pre:
        print('\tunimplemented!("Post instruction not implemented");')
    if high & 0x02 != 0:
        print('\tunimplemented!("Write-back not implemented");')
        
def write_instruction(high, low):
    print("#[allow(unreachable_code, unused_variables)]")
    print(
        "fn arm_%03x(_cpu: &mut ARM7TDMI, _io: &mut Interconnect, instr: u32) {"
        % (high * 16 + low)
    )

    if (high & 0xE0) == 0xA0: # B/BL
        write_branch(high, low)
    elif high == 0x12 and low == 1: # BX
        write_branch_exchange()
    elif (high & 0xD9) == 0x10: # PSR transfer
        write_psr(high, low)
    elif (high & 0xC0) == 0x00: # ALU
        write_alu(high, low)
    elif (high & 0xC0) == 0x40: # SDT
        write_sdt(high, low)
    else:
        print("\tunimplemented!(\"{:08x}\", instr);")

    print("}\n")

for high in range(0x0, 0x100):
    for low in range(0x0, 0x10):
        write_instruction(high, low)

print("const ARM_INSTRUCTIONS: [fn(&mut ARM7TDMI, &mut Interconnect, u32); 4096] = ")
print("[" + ", ".join(["arm_%03x" % i for i in range(0x0, 0x1000)]) + "];")
