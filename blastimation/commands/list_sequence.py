import sys

from blastimation.rom import rom

start = int(sys.argv[1], 16)
end = int(sys.argv[2], 16)

print("Looking for sequence in [0x%06X - 0x%06X]" % (start, end))

rom.load("blastcorps.us.v11.assets.yaml")

blast_type = None

addresses = []

for i in rom.images.keys():
    if start <= i <= end:
        print("0x%06X" % i, rom.images[i].blast.name)

        addresses.append("0x%06X" % i)

        if not blast_type:
            blast_type = rom.images[i].blast
        else:
            assert blast_type == rom.images[i].blast

addr_str = ", ".join(addresses)
print(f"    - [{addr_str}]")
