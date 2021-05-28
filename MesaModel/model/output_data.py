import os

import pandas as pd
from multiprocessing import Lock

mutex = Lock()


class OutputDataWriter:
    def __init__(self, output_filepath):
        self.output_filepath = output_filepath
        self.data = pd.DataFrame(
            columns=[
                "start_maths",
                "student_id",
                "class_id",
                "N_in_class",
                "Ability",
                "Inattentiveness",
                "hyper_impulsive",
                "Deprivation",
                "end_maths",
            ]
        )

    def write_data(self, agent_df, class_id, class_size):
        # Add class id and size into each row of data frame
        agent_df["class_id"] = class_id
        agent_df["N_in_class"] = class_size

        # Reorder columns to match our data
        agent_df = agent_df[self.data.columns]

        # Append to data frame
        self.data = self.data.append(agent_df)

        # Mutex is for parallel batchrunner
        with mutex:
            if not os.path.exists(self.output_filepath):
                self.data.to_csv(self.output_filepath, index=False, mode="a")
            else:
                self.data.to_csv(
                    self.output_filepath, index=False, mode="a", header=False
                )
