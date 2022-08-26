import time
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpContinuous, PULP_CBC_CMD, LpStatus, value
from pandas import DataFrame
from src.helpers import get_cost


def get_fixed_cost():
    return 10_000_000


class Dairon:
    problem: LpProblem = {}
    time = 0.0

    def __init__(self, data):
        self.data = data
        self.towns = self.data['towns']
        self.centers = self.data['centers']
        self.treatments = self.data['treatments']
        self.types = self.data['types']
        self.total_towns = [i for i in range(len(self.towns))]  # i
        self.total_centers = [i for i in range(len(self.centers))]  # j
        self.total_treatments = [i for i in range(len(self.treatments))]  # k
        self.total_types = [i for i in range(len(self.types))]  # l

    def make(self):
        self.set_problem()

        x = LpVariable.dicts('X', (
            self.total_towns,
            self.total_centers,
            self.total_types
        ), 0, None, LpContinuous)

        y = LpVariable.dicts('Y', (
            self.total_centers,
            self.total_treatments,
            self.total_types,
        ), 0, None, LpContinuous)

        w = LpVariable.dicts('W', (
            self.total_centers,
        ), 0, None, LpBinary)

        self.set_objective(lpSum(
            [x[i][j][l] * get_cost(self.data['transport_costs_from_town_to_center'], town['name'], center['name'])
             for i, town in enumerate(self.towns) for j, center in enumerate(self.centers) for l, type_ in
             enumerate(self.types)]) + lpSum(
            [y[j][k][l] * get_cost(self.data['transport_costs_from_center_to_treatment'], center['name'],
                                   treatment['name'])
             for j, center in enumerate(self.centers) for k, treatment in enumerate(self.treatments) for l, type_ in
             enumerate(self.types)]) + lpSum([w[j] * center['cost'] for j, center in enumerate(self.centers)]))

        self.set_constraints(x, y, w)

        return self

    def set_objective(self, objective):
        self.problem += objective

    def set_constraints(self, x, y, w):
        for i, town in enumerate(self.towns):
            self.problem += lpSum([x[i][j][l] for j in range(len(self.centers)) for l in range(len(self.types))]) == \
                            town['trash_amount']

        for j, center in enumerate(self.centers):
            self.problem += lpSum([x[i][j][l] for i in range(len(self.towns)) for l in range(len(self.types))]) <= \
                            center['capacity'] * w[j]
        for j, center in enumerate(self.centers):
            self.problem += lpSum(
                [x[i][j][l] for i in range(len(self.towns)) for l in range(len(self.types))]) == lpSum(
                [y[j][k][l] for k in range(len(self.treatments)) for l in range(len(self.types))])

        self.problem += lpSum([w[j] for j in range(len(self.centers))]) == len(self.treatments)

        for k, treatment in enumerate(self.treatments):
            for l, type_ in enumerate(self.types):
                self.problem += lpSum([type_['percentage'] * y[j][k][l] for j in range(len(self.centers))]) <= \
                                treatment['material_capacity'][type_['name']]

        return self

    def solve(self, message=False):
        self.time = time.time()
        self.problem.solve(PULP_CBC_CMD(msg=message))
        self.time = time.time() - self.time

        return self

    def get_status(self):
        return LpStatus[self.problem.status]

    def get_objective(self):
        return value(self.problem.objective)

    def get_variables(self):
        return self.problem.variables()

    def set_problem(self):
        self.problem = LpProblem("Minimize_costs", LpMinimize)

    def get_problem(self):
        return self.problem

    def to_json(self):
        variables = []

        for variable in self.get_variables():
            if variable.varValue != 0:
                variables.append({
                    'name': variable.name,
                    'value': variable.varValue
                })

        return {
            'status': self.get_status(),
            'objective': self.get_objective(),
            'time': round(self.time, 4),
            'results': variables
        }

    def to_dataframe(self):
        variables = list(map(lambda x: {'name': x.name, 'value': x.varValue}, self.get_variables()))
        dataframe = DataFrame(list(filter(lambda x: x['value'] != 0, variables)))

        return dataframe
