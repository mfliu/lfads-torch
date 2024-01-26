from collections import namedtuple

SessionBatch = namedtuple(
    "SessionBatch",
    [
        "encod_data",
        "recon_data",
        "ext_input",
        "truth",
        "sv_mask",
        "recon_region_map",
    ],
)

SessionOutput = namedtuple(
    "SessionOutput",
    [
        "output_params",
        "factors",
        "ic_mean",
        "ic_std",
        "co_means",
        "co_stds",
        "gen_states",
        "gen_init",
        "gen_inputs",
        "con_states",
    ],
)
