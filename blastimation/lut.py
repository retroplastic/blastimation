from blastimation.blast import Blast, blast_get_lut_size

luts = {
    128: {},
    256: {}
}


def get_last_lut(blast: Blast) -> int:
    lut_size = blast_get_lut_size(blast)
    lut_keys = list(luts[lut_size].keys())
    lut_keys.sort()
    return lut_keys[-1]