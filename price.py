from __future__ import division

import xml.etree.ElementTree as ET
import argparse
import json

circuit_bill = {}
xml_root = None
detailed = False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="The logisim file")
    parser.add_argument("circuit_name", help="The name of the circuit to calculate the price.")
    parser.add_argument("-d", "--detailed", help= "Creates a more detailed price glossary.", action="store_true")
    parser.add_argument("-o", "--output", help= "The file to dump the prices to, if ommited it will print the result to the stdout.")

    args = parser.parse_args()

    global xml_root
    global detailed

    input_file = args.file # "s-mips.circ"
    output_file = args.output # "result.json"
    circuit_name = args.circuit_name # "S-MIPS"
    detailed = args.detailed #False

    xml_root = ET.parse(input_file).getroot()

    _main = xml_root.find("./circuit[@name='{}']".format(circuit_name))
    if _main is None:
        print("There is no circuit called {}".format(circuit_name))
        exit(1)

    get_circuit_info(_main)

    if output_file is None:
        print(json.dumps(circuit_bill, indent=4))
    else:
        json.dump(circuit_bill, open(output_file,"w"), indent=4)

def bill(input_file, circuit_name):
    global xml_root
    global detailed

    xml_root = ET.parse(input_file).getroot()
    # circuits = xml_root.findall("circuit")

    _main = xml_root.find("./circuit[@name='{}']".format(circuit_name))
    if _main is None:
        raise ValueError("There is no circuit called {}".format(circuit_name))

    get_circuit_info(_main)

    return circuit_bill


def get_circuit_info(comp, level=0):
    if level > 100: exit(1)
    if is_default(comp): return get_default_circuit_info(comp)
    circuit_name = comp.get("name")
    # print("\t"*level + circuit_name)

    if circuit_name in circuit_bill:
        circuit_bill[circuit_name]["amount"]+=1
        return {"price": circuit_bill[circuit_name]["price"]}

    price = 0
    parts = xml_root.findall("./circuit[@name='{}']/comp".format(circuit_name))
    parts.extend(xml_root.findall("./circuit[@name='{}']/wire".format(circuit_name)))

    circuit_bill[circuit_name] = {"price": 0, "amount": 1, "parts":{}}

    for c in parts:
        info = get_circuit_info(c, level+1)
        price += info["price"]
        comp_id = get_comp_id(c)[1]
        if comp_id in circuit_bill[circuit_name]["parts"]:
            circuit_bill[circuit_name]["parts"][comp_id]["amount"]+=1
            if detailed:
                circuit_bill[circuit_name]["parts"][comp_id]["units"].append(info)
            circuit_bill[circuit_name]["parts"][comp_id]["total cost"]+=info["price"]
        else:
            data = {"amount": 1, "total cost":info["price"]}
            if detailed: data["units"] = [info]
            circuit_bill[circuit_name]["parts"][comp_id]= data

    circuit_bill[circuit_name]["price"]=price
    return {"price": price}

def is_default(comp):
    return comp.get("lib") or comp.tag=="wire"

def get_comp_id(comp):
    if is_default(comp):
        if comp.tag == "wire":
            key = ("0","Wire")
        else:
            key = (comp.get("lib"), comp.get("name"))
    else:
        key = ("-1" , comp.get("name"))

    return key

def get_default_circuit_info(comp):
    key = get_comp_id(comp)
    if comp.tag == "wire":
        info = {"from": comp.get("from"), "to": comp.get("to")}
    else:
        info = {}
        for prop in comp.findall("a"):
            info[prop.get("name")] = prop.get("val")

    info["price"] = calculate_price(key, info)

    return info


def calculate_price(key, info):

    def get_value(key,val):
        return int(info.get(key,val))

    price = 0

    if   key == ('0', 'Wire'):
        price = 0
    elif key == ('6', 'Text'):
        price = 0
    elif key == ('0', 'Splitter'):
        price = 0
    elif key == ('0', 'Tunnel'):
        price = 0
    elif key == ('0', 'Pin'):
        price = 1 if "pull" in info else 0
    elif key == ('0', 'Probe'):
        price = 0
    elif key == ('0', 'Pull Resistor'):
        price = 0
    elif key == ('0', 'Clock'):
        price = 1
    elif key == ('0', 'Constant'):
        price = 0
    elif key == ('0', 'Power'):
        price = 0
    elif key == ('0', 'Ground'):
        price = 0
    elif key == ('0', 'Transistor'):
        price = 2
    elif key == ('0', 'Transmission Gate'):
        price = 4
    elif key == ('0', 'Bit Extender'):
        price = get_value("in_width",8)+get_value("out_width",16)

    elif key == ('1', 'NOT Gate'):
        w = get_value("width", 1)
        price = 2*w
    elif key == ('1', 'Buffer'):
        w = get_value("width", 1)
        price = 2*w
    elif key == ('1', 'AND Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w
    elif key == ('1', 'OR Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w
    elif key == ('1', 'NAND Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w + 2*w
    elif key == ('1', 'NOR Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w + 2*w
    elif key == ('1', 'XOR Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w
    elif key == ('1', 'XNOR Gate'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+1)*w + 2*w
    elif key == ('1', 'Odd Parity'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+4)*w
    elif key == ('1', 'Even Parity'):
        w = get_value("width", 1)
        price = (get_value("inputs",5)+4)*w
    elif key == ('1', 'Controlled Buffer'):
        w = get_value("width", 1)
        price = 3*w
    elif key == ('1', 'Controlled Inverter'):
        w = get_value("width", 1)
        price = 3*w

    elif key == ('2', 'Multiplexer'):
        w = get_value("width", 1)
        s = get_value("select",1)
        price = (2**s - 1) * w * 10
    elif key == ('2', 'Demultiplexer'):
        w = get_value("width", 1)
        s = get_value("select",1)
        price = (2**s - 1) * w * 7
    elif key == ('2', 'Decoder'):
        s = get_value("select",1)
        price = 3*s**2 - s
    elif key == ('2', 'Priority Encoder'):
        s = get_value("select",3)
        n = 2**s
        price = n**2 + 3*n + s * n // 2
    elif key == ('2', 'BitSelector'):
        w = get_value("width", 8)
        o = get_value("group",1)
        price = w + o

    elif key == ('3', 'Adder'):
        w = get_value("width", 8)
        price = 4*w
    elif key == ('3', 'Subtractor'):
        w = get_value("width", 8)
        price = 4*w
    elif key == ('3', 'Multiplier'):
        w = get_value("width", 8)
        price = 4*w**2
    elif key == ('3', 'Divider'):
        w = get_value("width", 8)
        price = 4*w**2
    elif key == ('3', 'Negator'):
        w = get_value("width", 8)
        price = 2*w
    elif key == ('3', 'Comparator'):
        w = get_value("width", 8)
        price = 16+4*w
    elif key == ('3', 'Shifter'):
        w = get_value("width", 8)
        price = w**2
    elif key == ('3', 'BitAdder'):
        w = get_value("width", 8)
        price = 4*w
    elif key == ('3', 'BitFinder'):
        w = get_value("width", 8)
        price = 4*w

    elif key == ('4', 'D Flip-Flop'):
        price = 24
    elif key == ('4', 'T Flip-Flop'):
        price = 12
    elif key == ('4', 'J-K Flip-Flop'):
        price = 12
    elif key == ('4', 'S-R Flip-Flop'):
        price = 6
    elif key == ('4', 'Register'):
        w = get_value("width", 8)
        price = 24*w
    elif key == ('4', 'Counter'):
        w = get_value("width", 8)
        price = 28*w
    elif key == ('4', 'Shift Register'):
        w = get_value("width", 1)
        price = 40*w
    elif key == ('4', 'Random'):
        w = get_value("width", 8)
        price = 5*w
    elif key == ('4', 'RAM'):
        a = get_value("addrWidth", 8)
        w = get_value("dataWidth", 8)
        price = 2**a*w*8
    elif key == ('4', 'ROM'):
        a = get_value("addrWidth", 8)
        w = get_value("dataWidth", 8)
        price = 2**a*w*0.5

    elif key == ('5', 'Button'):
        price = 2
    elif key == ('5', 'Joystick'):
        price = 3000
    elif key == ('5', 'Keyboard'):
        price = 3000
    elif key == ('5', 'LED'):
        price = 10
    elif key == ('5', '7-Segment Display'):
        price = 100
    elif key == ('5', 'Hex Digit Display'):
        price = 100
    elif key == ('5', 'DotMatrix'):
        c = get_value("matrixcols", 5)
        r = get_value("matrixrows", 7)
        price = c*r*0.01
    elif key == ('5', 'TTY'):
        c = get_value("cols", 32)
        r = get_value("rows", 8)
        price = c*r*0.05
    else:
        print("Unknown element {}".format(key))

    return price // 1000

if __name__ == '__main__':
    main()
