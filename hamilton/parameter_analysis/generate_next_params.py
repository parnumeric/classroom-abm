import dataclasses
import os
import shutil
import sys

this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(this_dir)
sys.path.append(os.path.join(this_dir, "../../MesaModel"))
sys.path.append(os.path.join(this_dir, "../parameter_input"))

from model.data_types import ModelParamType, DEFAULT_MODEL_PARAMS, VARIABLE_PARAM_NAMES
import lhs_sampling
import merge_repeats
import plot_correlations

CUSTOM_ROUNDING = {
    "home_learn_factor": 7,
    "conformity_factor": 9,
    "maths_ticks_mean": 0,
}

CUSTOM_LIMITS = {"random_select": (1, None)}

CUSTOM_PERCENTAGE_CHANGE = {"random_select": 50}

if __name__ == "__main__":
    timestamp = sys.argv[1]
    output_csv = sys.argv[2]
    reframe_data_dir = sys.argv[3]
    parameterisation_data_dir = sys.argv[4]
    current_data_dir = os.path.join(parameterisation_data_dir, timestamp)
    if os.path.exists(current_data_dir):
        print(f"Directory {current_data_dir} already exists. Exiting.")
        sys.exit(1)

    os.mkdir(current_data_dir)
    shutil.copy(output_csv, current_data_dir)

    merged_dataframe = merge_repeats.merge_repeats(
        output_csv, output_dir=current_data_dir
    )
    plot_correlations.plot_correlations(current_data_dir, "lowest_to_highest_mses.csv")

    best_params = merged_dataframe.iloc[0]

    param_dict = {}
    valid_keys = dataclasses.asdict(DEFAULT_MODEL_PARAMS).keys()
    for k in best_params.keys():
        if k in valid_keys:
            percentage_change = CUSTOM_PERCENTAGE_CHANGE.get(k, 1)
            min_val, max_val = CUSTOM_LIMITS.get(k, (None, None))

            lower_bound = best_params[k] * (1 - percentage_change / 100)
            if min_val is not None:
                lower_bound = max(min_val, lower_bound)

            upper_bound = best_params[k] * (1 + percentage_change / 100)
            if max_val is not None:
                upper_bound = min(max_val, lower_bound)

            param_dict[k] = (lower_bound, upper_bound, CUSTOM_ROUNDING.get(k, 5))

    next_param_file = os.path.join(current_data_dir, f"next_lhs_params_{timestamp}.csv")
    lhs_sampling.generate_lhs_params(
        output_file=next_param_file, param_limits=param_dict
    )
