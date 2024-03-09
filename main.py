import tkinter
import statistics
import random

CITY_START_TEMPERATURE = 27
SEA_START_TEMPERATURE = 15
LAND_START_TEMPERATURE = 22
ICEBERG_START_TEMPERATURE = -10
FOREST_START_TEMPERATURE = 20


class Cell:
    def __init__(self, x, y, element_type, air_pollution=0):
        self.x = x
        self.y = y
        self.element_type = element_type  # options: sea,land,iceberg,forest or city
        self.wind_speed = self._init_wind_speed()  # in km/h
        self.wind_direction = self._init_wind_direction()  # one of: N, S, W, E
        self.cloud_precipitation = self._cloud_init()  # number from 0 to 1, 1 - is raining
        self.air_pollution = air_pollution

        self.temperature = self._init_temperature()  # in celsius degrees
        self.pollution_heat_factor = 0.6  # how much 100% pollution increase the temperature per day(in celsius degrees)
        self.rain_cold_factor = 0.4  # how much will the temperature decrease when raining
        self.city_pollution_factor = 0.14
        self.base_temperature = self._init_temperature()

        # variables for next generation calculation
        self.next_element_type = self.element_type
        self.next_wind_speed = self.wind_speed
        self.next_wind_direction = self.wind_direction
        self.next_cloud_precipitation = self.cloud_precipitation
        self.next_air_pollution = self.air_pollution
        self.next_temperature = self.temperature

    def _init_temperature(self):
        if self.element_type == "sea":
            return SEA_START_TEMPERATURE
        if self.element_type == "land":
            return LAND_START_TEMPERATURE
        if self.element_type == "iceberg":
            return ICEBERG_START_TEMPERATURE
        if self.element_type == "forest":
            return FOREST_START_TEMPERATURE
        if self.element_type == "city":
            return CITY_START_TEMPERATURE

    def _init_wind_direction(self):
        return random.choice(['N', 'W', 'E', 'S'])

    def _init_wind_speed(self):
        wind_speed = random.randint(0, 30)
        return wind_speed

    def _cloud_init(self):
        return round(random.uniform(0, 1), 1)

    def calculate_next_generation(self, world_map):

        # increase air pollution in cities
        if self.element_type == "city":
            self.next_air_pollution += self.city_pollution_factor
        # decrease air pollution in forests
        if self.element_type == "forest":
            self.next_air_pollution -= 0.4
            if self.next_air_pollution < 0:
                self.next_air_pollution = 0

        # increase air pollution if wind blows to my direction
        # change wind direction if neighbors wind speed is faster
        for direction in ['N', 'S', 'E', 'W']:
            neighbor = world_map.get_neighbor_cell(self.x, self.y, direction)
            neighbor_wind_speed = neighbor.get_wind_speed()
            if neighbor.get_wind_direction() == Utilities.opposite_direction(direction):
                self.next_air_pollution += neighbor.get_pollution() * neighbor_wind_speed
                if neighbor_wind_speed > self.next_wind_speed:
                    self.next_wind_direction = neighbor.get_wind_direction()

        # decrease pollution because blowing on neighbor
        self.next_air_pollution -= self.air_pollution * self.wind_speed
        if self.next_air_pollution < 0:
            self.next_air_pollution = 0

        # increase temperature due to high air pollution
        if self.air_pollution > 0.2:
            self.next_temperature += (self.pollution_heat_factor * self.air_pollution * (1 - self.temperature / 80))
        # if air pollution low decrease temperature toward basic temperature
        else:
            if self.temperature > self.base_temperature:
                self.next_temperature -= 0.5
            elif self.temperature < self.base_temperature:
                self.next_temperature += 0.5

        # if its raining clouds will disappear else chance of rain is increase by 10% in 50% cases
        # raining decrease temperature and decrease pollution
        if self.cloud_precipitation >= 1:
            self.next_cloud_precipitation = 0
            self.next_temperature -= (self.rain_cold_factor * (1 - self.temperature / -10))
            self.next_air_pollution = self.next_air_pollution/1.3
        elif random.random() > 0.5:
            self.next_cloud_precipitation += 0.1

        # effect of temperature changing
        if self.element_type == "iceberg" and self.next_temperature >= 0:
            self.next_element_type = "sea"
        if self.element_type == "sea" and self.next_temperature < 0:
            self.next_element_type = "iceberg"
        if self.element_type == "forest" and self.next_temperature > 50:
            self.next_element_type = "land"
        if self.element_type == "forest" and self.next_air_pollution >= 1:
            self.next_element_type = "land"

    def apply_next_generation(self):
        self.temperature = round(self.next_temperature, 2)
        self.wind_speed = self.next_wind_speed
        self.wind_direction = self.next_wind_direction

        self.cloud_precipitation = self.next_cloud_precipitation
        self.air_pollution = round(self.next_air_pollution, 2)
        if self.air_pollution > 1:
            self.air_pollution = 1
        if self.air_pollution < 0:
            self.air_pollution = 0
        self.element_type = self.next_element_type

    def get_wind_direction(self):
        return self.wind_direction

    def get_wind_speed(self):
        return self.wind_speed

    def get_element(self):
        return self.next_element_type

    def get_temperature(self):
        return self.temperature

    def get_cloud(self):
        return self.cloud_precipitation

    def get_pollution(self):
        return self.air_pollution

    def get_cell_color(self):
        if self.element_type == "sea":
            return '#00A3FF'  # blue
        if self.element_type == 'iceberg':
            return '#FFFFFF'  # white
        if self.element_type == 'forest':
            return '#28AE89'  # green
        if self.element_type == 'city':
            return '#FFBF00'  # orange
        if self.element_type == 'land':
            return '#AB9584'  # brown

    def get_cell_text(self):
        temp = int(self.temperature)
        pollution = round(self.air_pollution * 100, 2)
        text = f"{temp}\u2103\n P:{pollution}%"
        return text


class Map:
    def __init__(self):
        self.rows = 20
        self.cols = 20
        self.cell_size = 50
        self.map_file = "map.txt"

        elements_map = self._read_elements_map()
        (self.cells, self.temperature_list, self.pollution_list) = self._create_cells(elements_map)

        self.temperature_average = statistics.mean(self.temperature_list)
        self.pollution_average = statistics.mean(self.pollution_list)
        self.city_temperature_list = []
        self.city_temperature_average = CITY_START_TEMPERATURE

    def _read_elements_map(self):
        element_map = Utilities.create_matrix(self.rows, self.cols)
        with open(self.map_file, 'r') as f:
            for y in range(self.rows):
                for x in range(self.cols):
                    element = f.read(1)
                    while element not in ['S', 'L', 'I', 'F', 'C']:
                        element = f.read(1)
                    if element == 'S':
                        element_map[x][y] = 'sea'
                    if element == 'L':
                        element_map[x][y] = 'land'
                    if element == 'I':
                        element_map[x][y] = 'iceberg'
                    if element == 'F':
                        element_map[x][y] = 'forest'
                    if element == 'C':
                        element_map[x][y] = 'city'
        return element_map

    def _create_cells(self, elements_map):
        cells_matrix = Utilities.create_matrix(self.rows, self.cols)
        temperature_list = []
        air_pollution_list = []

        for y in range(self.rows):
            for x in range(self.cols):
                cell = Cell(x, y, elements_map[x][y])
                cells_matrix[x][y] = cell
                temperature_list.append(cell.get_temperature())
                air_pollution_list.append(cell.get_pollution())
        return cells_matrix, temperature_list, air_pollution_list

    def get_rows(self):
        return self.rows

    def get_cols(self):
        return self.cols

    def get_cell_size(self):
        return self.cell_size

    def get_temperature_average(self):
        return self.temperature_average

    def get_pollution_average(self):
        return self.pollution_average

    def get_city_temperature_average(self):
        return self.city_temperature_average

    def get_neighbor_cell(self, cur_x, cur_y, direction):
        delta_x = 0
        delta_y = 0
        if direction == 'N':
            delta_y = -1
        if direction == 'S':
            delta_y = 1
        if direction == 'W':
            delta_x = -1
        if direction == 'E':
            delta_x = 1
        neighbor_x = (cur_x + delta_x) % self.cols
        neighbor_y = (cur_y + delta_y) % self.rows

        return self.cells[neighbor_x][neighbor_y]

    def update_next_gen(self):
        self.temperature_list = []
        self.pollution_list = []
        self.city_temperature_list = []

        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.cells[x][y]
                cell.calculate_next_generation(self)

        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.cells[x][y]
                cell.apply_next_generation()
                self.temperature_list.append(cell.get_temperature())
                self.pollution_list.append(cell.get_pollution())
                if cell.get_element() == 'city':
                    self.city_temperature_list.append(cell.get_temperature())

        self.temperature_average = statistics.mean(self.temperature_list)
        self.pollution_average = statistics.mean(self.pollution_list)
        self.city_temperature_average = statistics.mean(self.city_temperature_list)


class AutomatonSimulation:
    def __init__(self):
        self.refresh_rate = 60
        self.total_generations_num = 365
        self.current_generation = 1
        self.daily_temperature_list = []
        self.daily_air_pollution_list = []
        self.daily_city_temperature_list = []
        self.map = Map()
        self.rows = self.map.get_rows()
        self.cols = self.map.get_cols()
        self.canvas_cells = Utilities.create_matrix(self.rows, self.cols)
        self.cell_size = self.map.get_cell_size()
        self.height = self.rows * self.cell_size
        self.width = self.cols * self.cell_size

        self.root = tkinter.Tk()
        self.root.title("Cellular Automaton World Global Warming Simulation")
        self.label = tkinter.Label(self.root, text=f"Generation {self.current_generation}", font="bold")
        self.label.pack()
        self.sub_label = tkinter.Label(self.root, text=self.get_sub_label_text())
        self.sub_label.pack()
        self.canvas = tkinter.Canvas(self.root, height=self.height, width=self.width, bg="white")
        self.canvas.pack()

        self._create_canvas()
        self._update_canvas()

        self.root.after(self.refresh_rate, self.move_next_gen)
        self.root.mainloop()

    def _create_canvas(self):
        for y in range(self.rows):
            for x in range(self.cols):
                canvas_sq_id = self.canvas.create_rectangle(x*self.cell_size, y*self.cell_size, (x+1)*self.cell_size,
                                                            (y+1)*self.cell_size)
                canvas_text_id = self.canvas.create_text((x + 0.5) * self.cell_size, (y + 0.25) * self.cell_size,
                                                         font="Ariel 8 bold")
                self.canvas_cells[x][y] = (canvas_sq_id, canvas_text_id)

    def _update_canvas(self):
        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.map.cells[x][y]
                canvas_cell_color = cell.get_cell_color()
                canvas_cell_text = cell.get_cell_text()
                (canvas_sq_id, canvas_text_id) = self.canvas_cells[x][y]
                self.canvas.itemconfig(canvas_sq_id, fill=canvas_cell_color)
                self.canvas.itemconfig(canvas_text_id, text=canvas_cell_text)

    def move_next_gen(self):
        self.daily_temperature_list.append(self.map.get_temperature_average())
        self.daily_air_pollution_list.append(self.map.get_pollution_average())
        self.daily_city_temperature_list.append(self.map.get_city_temperature_average())
        if self.current_generation < self.total_generations_num:
            self.current_generation += 1
            self.map.update_next_gen()
            self._update_canvas()
            self.label.config(text=f"Generation {self.current_generation}")
            self.sub_label.config(text=self.get_sub_label_text())
            self.root.after(self.refresh_rate, self.move_next_gen)
        else:
            self.label.config(text=f"Generation {self.current_generation}, simulation finished")

    def get_sub_label_text(self):
        temperature_average = round(self.map.get_temperature_average(), 2)
        pollution_average = round(self.map.get_pollution_average()*100, 2)
        text = f"Temperature average: {temperature_average } \u2103   \t Air pollution average: {pollution_average}%\n"
        return text

    def get_daily_temp_list(self):
        return self.daily_temperature_list

    def get_daily_pollution_list(self):
        return self.daily_air_pollution_list

    def get_daily_city_temperature_list(self):
        return self.daily_city_temperature_list


class Utilities:
    @classmethod
    def create_matrix(cls, rows, columns):
        return [([0] * columns) for i in range(rows)]

    @classmethod
    def opposite_direction(cls, direction):
        if direction == "N":
            return "S"
        if direction == "S":
            return "N"
        if direction == "W":
            return "E"
        if direction == "E":
            return "W"


if __name__ == '__main__':
    print("main is running")
    simulation = AutomatonSimulation()
    daily_temp_list = simulation.get_daily_temp_list()
    yearly_temp_average = statistics.mean(daily_temp_list)
    yearly_temp_standard_deviation = statistics.pstdev(daily_temp_list)
    temp_file = open("daily_temperature_avg.txt", "w")
    temp_normalized_file = open("daily_temperature_avg_normalized","w")

    for data in daily_temp_list:
        temp_file.write(f'{data}\n')
        normalized_data = (data - yearly_temp_average)/yearly_temp_standard_deviation
        temp_normalized_file.write(f'{normalized_data}\n')
    temp_file.close()
    temp_normalized_file.close()

    daily_pollution_list = simulation.get_daily_pollution_list()
    yearly_pollution_avg = statistics.mean(daily_pollution_list)
    yearly_pollution_standard_deviation = statistics.pstdev(daily_pollution_list)
    pollution_f = open('daily_pollution_avg.txt', "w")
    pollution_normalized_f = open("daily_pollution_normalized.txt", "w")

    for data in daily_pollution_list:
        pollution_f.write(f'{data}\n')
        normalized_data = (data - yearly_pollution_avg)/yearly_pollution_standard_deviation
        pollution_normalized_f.write(f'{normalized_data}\n')
    pollution_f.close()
    pollution_normalized_f.close()

    daily_city_temperature_list = simulation.get_daily_city_temperature_list()
    yearly_city_temperature_avg = statistics.mean(daily_city_temperature_list)
    yearly_city_temp_st_deviation = statistics.mean(daily_city_temperature_list)
    city_temp_f = open("daily_city_temperature.txt", "w")
    city_temp_normalized_f = open("city_temp_normalized.txt", "w")
    for data in daily_city_temperature_list:
        city_temp_f.write(f"{data}\n")
        normalized_data = (data - yearly_city_temperature_avg)/yearly_city_temp_st_deviation
        city_temp_normalized_f.write(f"{normalized_data}\n")
    city_temp_f.close()
    city_temp_normalized_f.close()

    print("finished")
