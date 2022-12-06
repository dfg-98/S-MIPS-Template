#! /usr/bin/env python3

import os
import subprocess
import sys
import optparse


verbose_level = 0
verbose_level_all = 4
verbose_level_compile_detail = 3
verbose_level_test_detail = 2
verbose_level_test_basic_detail = 1


def print_verbose(verbose_level_required, *args):
    if verbose_level >= verbose_level_required:
        print(*args)


class TestCase:
    def __init__(self, test_name, file, expected_result, expected_speed=None):
        self.file = file
        self.expected_result = expected_result
        self.expected_speed = expected_speed
        self.test_name = test_name
        self.runned = False
        self.error = False

    def run(self, logisim, circ, template):
        result = ""
        cmd = [
            logisim,
            template,
            "-tty",
            "halt,tty,speed",
            "-load",
            self.file,
            "-sub",
            template,
            circ,
        ]
        try:
            print_verbose(
                verbose_level_test_detail, "Ejecutando el test: ", self.test_name
            )
            result = subprocess.run(cmd, stdout=subprocess.PIPE)
            self.runned = True
            if result.returncode != 0:
                print("Error al ejecutar test: ", self.test_name)
                print(result.stdout)
                print(result.stderr)
                self.error = True
                return
            output = bytes.decode(result.stdout)
            r = output.find("halted due to halt pin")
            self.result = output[:r].strip()
            s = output.find("Hz (")
            e = output.find(" ticks", s)
            self.speed = output[s + 4 : e]

        except subprocess.CalledProcessError as e:
            print("Error al ejecutar test: ", self.test_name)
            print(result.stdout)
            print(result.stderr)
            self.error = True

    def print(self):

        if self.error:
            print("El test no pudo ejecutarse correctamente")

        elif self.runned:
            status = self.result == self.expected_result
            print(
                "Resultado:",
                self.test_name,
                " ===============================================> ",
                "OK" if status else "FAIL",
            )
            print_verbose(
                verbose_level_test_detail,
                "Resultado Esperado: ",
                self.expected_result,
                "Resultado Obtenido: ",
                self.result,
            )
            status = self.speed <= self.expected_speed
            print(
                "Tiempo:",
                self.test_name,
                " ===============================================> ",
                "OK" if status else "FAIL",
            )
            print_verbose(
                verbose_level_test_detail,
                "Tiempo Esperado: ",
                self.expected_speed,
                "Tiempo Obtenido: ",
                self.speed,
            )

        else:
            print("Test:", self.test_name, "Debe correr el test antes")

        print(
            "---------------------------------------------------------------------------------------"
        )


class TestSuite:
    def __init__(self, dir, base_dir, circ, template):
        self.base_dir = base_dir
        self.circ = circ
        self.path = dir
        self.test = []
        self.template = template
        for file, path in self.searchAsmFiles():
            self.compile(file, path)
            expected = self.extractExpectedResult(path)
            excepted_time = self.extractExpectedSpeed(path)
            self.test.append(
                TestCase(
                    file,
                    os.path.join(self.base_dir, file, "Bank"),
                    expected,
                    excepted_time,
                )
            )

    def searchAsmFiles(self):
        for root, dirs, files in os.walk(self.path):
            print_verbose(verbose_level_all, "Buscando archivos .asm en: ", root)
            for file in files:
                try:
                    if file.endswith(".asm"):
                        print_verbose(verbose_level_all, "Archivo encontrado: ", file)
                        path = os.path.join(root, file)
                        yield file[:-4], path
                except Exception as e:
                    print("e")

    def compile(self, file, path):
        base_dir = os.path.join(self.base_dir, file)
        print_verbose(verbose_level_all, "Creando directorio: ", base_dir)
        try:
            os.mkdir(base_dir)
        except FileExistsError as e:
            print_verbose(verbose_level_all, "Directorio existente: ", base_dir)
        print_verbose(verbose_level_all, "Compilando: ", path)
        status = os.system(f"./assembler.py {path} -o {base_dir}")
        if status != 0:
            print("Error al compilar: ", path)

    def extractExpectedResult(self, path):

        with open(path, "r") as file:
            content = file.readlines()

        read = False
        expected = ""

        for line in content:
            if line.startswith("#prints"):
                expected = line[8:].strip()
                break
        print_verbose(verbose_level_all, "Resultado esperado del test: ")
        print_verbose(verbose_level_all, expected)
        return expected

    def extractExpectedSpeed(self, path):

        with open(path, "r") as file:
            content = file.readlines()

        read = False
        expected = ""

        for line in content:
            if line.startswith("#limit"):
                expected = line[7:].strip()
                break
        print_verbose(verbose_level_all, "Tiempo esperado del test: ")
        print_verbose(verbose_level_all, expected)
        return expected

    def run_all(self):
        for test in self.test:
            test.run("logisim", self.circ, self.template)
            test.print()

    def run_test(self, test_name):
        for test in self.test:
            if test.name == test_name:
                test.run("logisim", self.circ, self.template)
                test.print()


if __name__ == "__main__":
    usage = "usage: %prog tests_dir circuit [options]"

    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-o",
        "--out",
        dest="output_folder",
        type="string",
        default=".",
        help="Specify output folder to compile tests",
    )
    parser.add_option(
        "-t",
        "--template",
        dest="template",
        type="string",
        default="s-mips-template.circ",
        help="The template .circ file without specific implementation",
    )
    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        type="int",
        default=0,
        help="Verbose debug mode",
    )
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error("Incorrect command line arguments")
        sys.exit(1)

    verbose_level = options.verbose

    output_folder = options.output_folder
    template = options.template
    input_dir = args[0]
    circ = args[1]

    try:
        os.mkdir(output_folder)
    except FileExistsError as e:
        print_verbose(verbose_level_all, "Directorio existente: ", output_folder)

    if not os.path.exists(template):
        print("El archivo de template no existe")
        sys.exit(1)

    test_suite = TestSuite(input_dir, output_folder, circ, template)
    test_suite.run_all()
