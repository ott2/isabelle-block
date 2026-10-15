#!/usr/bin/env python3
"""Apply the 2026-07-03 wrap-chain rename to prose docs (word-boundary +
derived-fact lookahead).

    bin/rename-wrap-in-docs.py FILE [FILE ...]

The mapping below is the durable record of the rename ([ls-rename]): the ten
theory renames and the 54 lemma/constant tag strips.  It contains ONLY
current-construction names, so applying it to a doc updates the surviving plant
construction's names while leaving the deleted shift/transpose names
(`EncodingWrap_Transpose*`, `wrap_delta_tr`, `encoding_wrap_tr`, `wf_tr`, ...)
intact as historical references.  Do NOT run this over `history/` (frozen
chronology).
"""
import re
import sys

THEORIES = {
    "EncodingWrap_Base": "Wrap_Base",
    "EncodingWrap_Plant": "Wrap_Defs",
    "EncodingWrap_PlantReset": "Wrap_Reset",
    "EncodingWrap_PlantRun": "Wrap_Run",
    "EncodingWrap_PlantEncoder": "Wrap_Encoder",
    "EncodingWrap_PlantForcing": "Wrap_Forcing",
    "EncodingWrap_PlantCanonical": "Wrap_Canonical",
    "EncodingWrap_PlantLanguage": "Wrap_Language",
    "EncodingWrap_PlantTime": "Wrap_Time",
    "EncodingWrap_PlantClassical": "Wrap_Speedup",
}
LEMMAS = {
    "det_B": "wrap_det", "wf_B": "wrap_wf",
    "encoding_wrap_B": "encoding_wrap", "wrap_delta_B": "wrap_delta",
    "wrap_time_B": "wrap_time", "wrap_language_B": "wrap_language",
    "wrap_language_forward_B": "wrap_language_forward",
    "wrap_language_reverse_B": "wrap_language_reverse",
    "wrap_run_delta_tr": "wrap_run_delta", "lift_M_config_tr": "lift_M_config",
    "wrap_plant_done_delta_tr": "wrap_plant_done_delta",
    "wrap_delta_B_cases": "wrap_delta_cases",
    "wrap_delta_B_W_Run_source_only_run": "wrap_delta_W_Run_source_only_run",
    "wrap_delta_B_W_Run_target_from_W_Disp": "wrap_delta_W_Run_target_from_W_Disp",
    "wrap_delta_B_W_Disp_source_only_disp": "wrap_delta_W_Disp_source_only_disp",
    "wrap_delta_B_non_W_Run_det": "wrap_delta_non_W_Run_det",
    "wrap_delta_B_full_buf_in_close": "wrap_delta_full_buf_in_close",
    "wrap_delta_B_partial_buf_in_nonempty_end": "wrap_delta_partial_buf_in_nonempty_end",
    "encoder_phase_terminates_B": "encoder_phase_terminates",
    "init_to_mid_zero_B": "init_to_mid_zero",
    "init_to_mid_buf_extending_B": "init_to_mid_buf_extending",
    "init_to_mid_buf_partial_B": "init_to_mid_buf_partial",
    "init_to_post_encoder_relpow_B": "init_to_post_encoder_relpow",
    "mid_buf_close_step_B": "mid_buf_close_step",
    "mid_buf_extend_step_B": "mid_buf_extend_step",
    "mid_encoder_step_B": "mid_encoder_step",
    "mid_encoder_step_relpow_B": "mid_encoder_step_relpow",
    "mid_encoder_iter_relpow_B": "mid_encoder_iter_relpow",
    "mid_to_post_B": "mid_to_post", "mid_to_post_empty_B": "mid_to_post_empty",
    "mid_to_post_partial_B": "mid_to_post_partial",
    "mid_to_post_partial_relpow_B": "mid_to_post_partial_relpow",
    "run_step_forward_B": "run_step_forward", "run_step_reverse_B": "run_step_reverse",
    "run_steps_forward_B": "run_steps_forward", "run_steps_reverse_B": "run_steps_reverse",
    "run_steps_forward_relpow_B": "run_steps_forward_relpow",
    "wrap_accept_canonical_factor_B": "wrap_accept_canonical_factor",
    "wrap_full_block_pack_contract_B": "wrap_full_block_pack_contract",
    "wrap_partial_block_pack_contract_B": "wrap_partial_block_pack_contract",
    "wrap_close_step_forces_pack_B": "wrap_close_step_forces_pack",
    "wrap_partial_close_step_forces_pack_B": "wrap_partial_close_step_forces_pack",
    "wrap_W_Run_persistent_B": "wrap_W_Run_persistent",
    "wrap_W_Disp_then_W_Run_B": "wrap_W_Disp_then_W_Run",
    "wrap_step_W_Disp_to_W_Run_B": "wrap_step_W_Disp_to_W_Run",
    "wrap_first_W_Run_decomp_B": "wrap_first_W_Run_decomp",
    "wrap_step_unique_non_run_B": "wrap_step_unique_non_run",
    "wrap_path_det_non_run_B": "wrap_path_det_non_run",
    "linear_speedup_HU_12_3_nae_B": "linear_speedup_HU_12_3_nae",
    "linear_speedup_HU_12_3_dae_B": "linear_speedup_HU_12_3_dae",
    "linear_speedup_HU_12_4_nae_B": "linear_speedup_HU_12_4_nae",
    "linear_speedup_HU_12_4_dae_B": "linear_speedup_HU_12_4_dae",
    "linear_speedup_form_1_raw_nae_B": "linear_speedup_form_1_raw_nae",
    "linear_speedup_form_1_raw_dae_B": "linear_speedup_form_1_raw_dae",
}


def main():
    mapping = {**THEORIES, **LEMMAS}
    # longest OLD first: keeps `wrap_delta_B_cases` from being pre-empted by the
    # `wrap_delta_B` stem rule (belt-and-braces; \b already separates them).
    pairs = sorted(mapping.items(), key=lambda kv: -len(kv[0]))
    for path in sys.argv[1:]:
        with open(path) as fh:
            text = fh.read()
        orig = text
        n = 0
        for old, new in pairs:
            text, cnt = re.subn(r"\b" + re.escape(old) + r"(?![A-Za-z0-9])",
                                new, text)
            n += cnt
        if text != orig:
            with open(path, "w") as fh:
                fh.write(text)
        print(f"  {path}: {n} replacement(s)")


if __name__ == "__main__":
    main()
