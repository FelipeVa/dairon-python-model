from src.classes.dairon import Dairon
from src.helpers import json_loader


def main():
    data = json_loader("dairon")
    dairon = Dairon(data).make().solve()

    return print(dairon.to_dataframe())


if __name__ == '__main__':
    main()
