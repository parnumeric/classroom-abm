import math

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid
from mesa.time import RandomActivation
from scipy import stats as stats

from .data_types import TeacherParamType, PupilParamType, PupilLearningState
from .Pupil import Pupil
from .utils import (
    compute_ave,
    compute_ave_disruptive,
    get_num_disruptors,
    get_num_learning,
    get_grid_size,
)


class SimModel(Model):
    def __init__(
        self,
        all_data,
        model_initial_state,
        output_data_writer,
        class_id=None,
        teacher_params=None,
        pupil_params=None,
        model_params=None,
        **kwargs,
    ):
        self.data = all_data
        self.model_state = model_initial_state
        self.output_data_writer = output_data_writer
        self.class_id = class_id
        self.teacher_params = teacher_params
        self.pupil_params = pupil_params
        self.model_params = model_params
        self.write_file = False

        if "teacher_quality" in kwargs and "teacher_control" in kwargs:
            self.teacher_params = TeacherParamType(
                kwargs["teacher_quality"], kwargs["teacher_control"]
            )
        elif not self.teacher_params:
            self.teacher_params = TeacherParamType(0, 0)

        if (
            "pupil_inattentiveness" in kwargs
            and "pupil_hyper_impulsivity" in kwargs
            and "pupil_attention_span" in kwargs
        ):
            self.pupil_params = PupilParamType(
                kwargs["pupil_inattentiveness"],
                kwargs["pupil_hyper_impulsivity"],
                kwargs["pupil_attention_span"],
            )
        elif not self.pupil_params:
            self.pupil_params = PupilParamType(0, 0, 2)

        if "class_id" in kwargs:
            self.class_id = kwargs["class_id"]
        elif not self.class_id:
            self.class_id = 489

        if "write_file" in kwargs:
            self.write_file = kwargs["write_file"]

        self.class_data = self.data.get_class_data(self.class_id)
        self.class_size = len(self.class_data)

        self.schedule = RandomActivation(self)

        # Calculate steps per day and holidays
        self.is_school_time = True
        # 330 minutes is time awake at home: 5.5 hours * 60 minutes
        self.ticks_per_day = 330 + self.model_params.ticks_per_school_day
        total_days = 317  # days from 1st September to 16th July
        self.total_steps = self.ticks_per_day * total_days

        self.holiday_week_numbers = self.calculate_holiday_weeks(
            total_days,
            self.model_params.number_of_holidays,
            self.model_params.weeks_per_holiday,
        )
        print(self.holiday_week_numbers)

        # Create grid with torus = False - in a real class students at either ends of classroom don't interact
        self.grid_params = get_grid_size(
            len(self.class_data), self.model_params.group_size
        )
        self.grid = SingleGrid(
            self.grid_params.width, self.grid_params.height, torus=False
        )

        sorted_pupils = []
        if self.model_params.group_by_ability:
            sorted_pupils = self.class_data.sort_values("Ability")
        else:
            sorted_pupils = self.class_data.sample(frac=1)

        # Set up agents
        pupil_counter = 0
        for i in range(self.grid_params.n_groups):
            group_size = self.model_params.group_size
            if i >= self.grid_params.n_full_groups:
                group_size -= 1

            group_pupils = sorted_pupils.iloc[
                pupil_counter : pupil_counter + group_size
            ]
            group_x = math.floor(i / self.grid_params.n_group_rows)
            group_y = i % self.grid_params.n_group_rows

            for j, row in enumerate(group_pupils.iterrows()):
                index, pupil_data = row
                # Initial learning state for all student is random
                learning_state = self.random.choice(list(PupilLearningState))

                # Work out position on grid
                x = (group_x * self.grid_params.group_width + group_x) + math.floor(
                    j / self.grid_params.group_height
                )
                y = (group_y * self.grid_params.group_height + group_y) + (
                    j % self.grid_params.group_height
                )

                # create agents from data
                agent = Pupil(
                    (x, y),
                    self,
                    pupil_data.student_id,
                    learning_state,
                    pupil_data.Inattentiveness,
                    pupil_data.hyper_impulsive,
                    pupil_data.Deprivation,
                    pupil_data.start_maths,
                    pupil_data.Ability,
                )
                # Place Agents on grid
                self.grid.position_agent(agent, x, y)
                self.schedule.add(agent)

            pupil_counter += group_size

        # Collecting data while running the model
        self.model_datacollector = DataCollector(
            model_reporters={
                "Learning Students": get_num_learning,
                "Disruptive Students": get_num_disruptors,
                "Average End Math": compute_ave,
                "disruptiveTend": compute_ave_disruptive,
            }
        )

        self.agent_datacollector = DataCollector(
            agent_reporters={
                "student_id": "student_id",
                "end_maths": "e_math",
                "start_maths": "s_math",
                "Ability": "ability",
                "Inattentiveness": "inattentiveness",
                "hyper_impulsive": "hyper_impulsive",
                "Deprivation": "deprivation",
            }
        )

        self.running = True

    @staticmethod
    def calculate_holiday_weeks(total_days, number_of_holidays, weeks_per_holiday):
        """Calculate which weeks should be holidays given the total number of
        days from start to end of the school year, and the number and length
        of holidays

        Returns an array of week numbers which are holidays
        """
        n_terms = number_of_holidays + 1
        n_holiday_weeks = number_of_holidays * weeks_per_holiday
        n_school_weeks = math.ceil(total_days / 7) - n_holiday_weeks
        min_weeks_per_term = math.floor(n_school_weeks / n_terms)
        remainder_weeks = n_school_weeks % n_terms

        weeks_per_term = []
        for i in range(n_terms):
            term_weeks = min_weeks_per_term
            if i < remainder_weeks:
                term_weeks += 1
            weeks_per_term.append(term_weeks)

        holiday_week_numbers = []
        current_week = 0
        for term_weeks in weeks_per_term[:-1]:
            start_week = current_week + term_weeks
            holiday_week_numbers.extend(
                list(range(start_week, start_week + weeks_per_holiday))
            )
            current_week += term_weeks + weeks_per_holiday
        return holiday_week_numbers

    def update_school_time(self):
        time_in_day = self.schedule.steps % self.ticks_per_day

        # If currently in school, remain so until time in day is > ticks_per_school_day
        if self.is_school_time:
            if time_in_day < self.model_params.ticks_per_school_day:
                return
            else:
                self.is_school_time = False
        else:
            # Currently pupil is at home
            if time_in_day == 0:
                print(
                    f"Step: {self.schedule.steps}, start of day, ",
                )
                # A new day - is it a weekend or holiday?
                day_number = math.floor(self.schedule.steps / self.ticks_per_day)
                day_in_week = day_number % 7
                if day_in_week > 4:
                    print("Weekend")
                    # It's a weekend so remain at home
                    return
                else:
                    print(
                        "Weekday",
                    )
                    # Is it a holiday?
                    week_number = math.floor(day_number / 7)
                    if week_number not in self.holiday_week_numbers:
                        print("Term time")
                        self.is_school_time = True
                    else:
                        print("Holiday")
            else:
                # Not a new day so continue in home time
                return

    def step(self):
        # Reset counter of learning and disruptive agents
        self.model_state.learning_count = 0
        self.model_state.disruptive_count = 0

        # Advance the model by one step
        self.schedule.step()

        self.update_school_time()

        # collect data
        self.model_datacollector.collect(self)

        if self.schedule.steps == self.total_steps or self.running == False:
            self.running = False
            self.agent_datacollector.collect(self)
            agent_data = self.agent_datacollector.get_agent_vars_dataframe()
            self.output_data_writer.write_data(
                agent_data, self.class_id, self.class_size
            )
