import datetime
import sys

import click
from multilevel_analysis import run_multilevel_analysis

sys.path.append("../MesaModel")
from run import run_model
from model.data_types import TeacherParamType, PupilParamType


@click.command()
@click.option(
    "--input-file",
    "-i",
    default="../classes_input/test_input.csv",
    help="File path containing real data, relative to multilevel_analysis directory. Defaults to ../classes_input/test_input.csv",
)
@click.option(
    "--output-file",
    "-o",
    default=f"../classes_output/output{datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv",
    help="Output file path, relative to current working directory.",
)
@click.option(
    "--n-processors",
    "-p",  # 'np' is avoided given the meaning this already has in MPI contexts
    default=2,
    help="Number of processors to be used by the batchrunner",
)
@click.option(
    "--model-params",
    default="1,1",
    help="Comma separated model params in form: teacher_control,teacher_quality",
)
@click.option(
    "--test-mode",
    "-t",
    default=False,
    is_flag=True,
    help="Whether to run in test mode (only 10 ticks per day)",
)
def run_model_and_mlm(
    input_file,
    output_file,
    n_processors,
    model_params,
    test_mode
):
    run_model(input_file, output_file, n_processors, model_params=model_params, test_mode=test_mode)
    mean_squared_error = run_multilevel_analysis(input_file, output_file)
    print(f"Mean squared error: {mean_squared_error}")
    return mean_squared_error


if __name__ == "__main__":
    run_model_and_mlm()
