import ryaml

from blastimation.animation_comp import AnimationComp
from blastimation.comp import Composite, CompType
from blastimation.rom import rom


class Meta:
    def __init__(self):
        self.in_comp: list[int] = []
        self.comps: dict[int:Composite] = {}

        with open("meta.yaml", "r") as f:
            composites_yaml = ryaml.load(f)

        for comp_type_str, comp_list in composites_yaml["composites"].items():
            comp_type = getattr(CompType, comp_type_str)
            for addresses in comp_list:
                c = Composite()
                c.type = comp_type
                if isinstance(addresses[-1], str):
                    c.name = addresses[-1]
                    c.addresses = addresses[:-1]
                else:
                    c.addresses = addresses

                self.in_comp.extend(c.addresses)
                self.comps[c.start()] = c

                # Fix LUTs
                if c.start() in [0x0999E0]:
                    first_lut = rom.images[c.start()].lut
                    for addr in c.addresses:
                        rom.images[addr].lut = first_lut

        for comp_type_str, animations_dict in composites_yaml["composite_animations"].items():
            comp_type = getattr(CompType, comp_type_str)
            for animation_name, comps_list in animations_dict.items():
                animation_comp = AnimationComp()
                animation_comp.name = animation_name
                i = 0
                for addresses in comps_list:
                    c = Composite()
                    c.name = f"{animation_name}.{i}"
                    i += 1
                    c.addresses = addresses
                    c.type = comp_type

                    self.in_comp.extend(c.addresses)
                    animation_comp.comps.append(c)
                self.comps[animation_comp.start()] = animation_comp

                # Fix LUTs
                if animation_comp.start() in [0x1D0DF8, 0x281C90]:
                    first_lut = rom.images[animation_comp.start()].lut
                    for comp in animation_comp.comps:
                        for addr in comp.addresses:
                            rom.images[addr].lut = first_lut
