import math

from pycrunch.scheduling.sheduled_task import TestRunPlan


class TestRunScheduler():
    # Do not split up to 5 tasks
    threshold = 5

    def __init__(self, cpu_cores, threshold):
        self.cpu_cores = cpu_cores
        self.threshold = threshold

    def schedule_into_tasks(self, tests):
        list_of_tasks = []
        total_tests_to_run = len(tests)
        print(f'total_tests_to_run {total_tests_to_run}')
        if total_tests_to_run <= self.threshold:
            list_of_tasks.append(TestRunPlan(tests))
            return list_of_tasks

        avarage_per_core = total_tests_to_run / self.cpu_cores
        total_cores_to_use = 1
        tests_can_be_scheduled = 0
        if avarage_per_core < self.threshold:
            for x in range(1, self.cpu_cores):
                total_cores_to_use = x
                tests_can_be_scheduled += self.threshold
                if tests_can_be_scheduled > total_tests_to_run:
                    break
            print('smart', avarage_per_core)
        else:
            total_cores_to_use = self.cpu_cores
        print(f'tests_can_be_scheduled {tests_can_be_scheduled}')
        print(f'total_cores_to_use {total_cores_to_use}')
        tests_so_far = 0
        tests_scheduled_per_core_with_decimal = total_tests_to_run / total_cores_to_use
        print(f'tests_scheduled_per_core_with_decimal {tests_scheduled_per_core_with_decimal}')
        tests_to_run_on_single_core = math.ceil(tests_scheduled_per_core_with_decimal)
        print(f'rounded tests_to_run_on_single_core {tests_to_run_on_single_core}')
        for x in range(total_cores_to_use):
            from_index = tests_so_far
            to_index = tests_so_far + tests_to_run_on_single_core
            print(f'from:to -> {from_index}:{to_index}')
            spliced = tests[from_index:to_index]
            print(f'core {x}; spliced amount: {len(spliced)}')
            plan = TestRunPlan(spliced)
            list_of_tasks.append(TestRunPlan(spliced))
            tests_so_far += tests_to_run_on_single_core
        return list_of_tasks
