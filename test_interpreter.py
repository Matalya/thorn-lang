import unittest
from pathlib import Path
import copy
import tempfile

from thorn import SOURCE_SUFFIXES, format_runtime_error, thorn_source_path, run_source
from runtime import ThornList, ThornRuntimeError


class InterpreterTests(unittest.TestCase):
    def run_program(self, source):
        output = []
        run_source(source, output=output.append)
        return "".join(output)

    def test_expressions_variables_and_composite_strings(self):
        output = self.run_program(
            '''
            int result = 1 + 2 * 3;
            str message = c"The result is {result}";
            print(message);
            '''
        )
        self.assertEqual("The result is 7\n", output)

    def test_control_flow_and_compound_assignment(self):
        output = self.run_program(
            '''
            int total = 0;
            for (i from 0 to 4) {
                total += i;
            }
            if (total == 6) {
                print("yes", end = "");
            } else {
                print("no", end = "");
            }
            '''
        )
        self.assertEqual("yes", output)

    def test_functions_defaults_named_arguments_and_recursion(self):
        output = self.run_program(
            '''
            int factorial(int value) {
                if (value <= 1) { return 1; }
                return value * factorial(value - 1);
            }
            str greet(str name, str punctuation = "!") {
                return c"{name}{punctuation}";
            }
            print(factorial(5));
            print(greet(punctuation = "?", name = "Ada"));
            '''
        )
        self.assertEqual("120\nAda?\n", output)

    def test_runic_program_executes_with_runic_builtin(self):
        output = self.run_program(
            '''
            ᛁᚾᛏ factorial(ᛁᚾᛏ value) {
                ᛁᚠ (value <= 1) {
                    ᚱᛁᛏᚢᚱᚾ 1;
                }
                ᚱᛁᛏᚢᚱᚾ value * factorial(value - 1);
            }
            ᛋᛏᚱ name = "Matías";
            ᛁᚾᛏ answer = factorial(5);
            ᛈᚱᛁᚾᛏ(ᚳ"Hello, {name}!");
            ᛈᚱᛁᚾᛏ(ᚳ"5! is {answer}");
            ᛁᚠ (answer == 120) {
                ᛈᚱᛁᚾᛏ("The Thorn interpreter works!");
            } ᛖᛚᛋ {
                ᛈᚱᛁᚾᛏ("Something went wrong.");
            }
            '''
        )
        self.assertEqual(
            "Hello, Matías!\n5! is 120\nThe Thorn interpreter works!\n",
            output,
        )

    def test_list_methods_negative_indexes_and_slices(self):
        output = self.run_program(
            '''
            list(int | nil) values = [1, 2, 2, nil, 3];
            values.prepend(0);
            values.insert(9, 1);
            print(values.replace_at(8, 1));
            print(values[-1]);
            print(values.find_nth(2, 2));
            values.compress();
            print(values[1:4]);
            print(values.shorten(2));
            print(values);
            '''
        )
        self.assertEqual("9\n3\n4\n[8, 1, 2]\n[2, 3]\n[0, 8, 1, 2]\n", output)

    def test_array_capacity_fill_resize_and_slice(self):
        output = self.run_program(
            '''
            arr(int, 5) values = <1, 2>;
            print(values.length());
            print(values.capacity());
            values.append(3);
            values.fill(9);
            print(values);
            values.resize(3);
            print(values[1:]);
            print(values.capacity());
            '''
        )
        self.assertEqual(
            "2\n5\n<1, 2, 3, 9, 9>\n"
            "warning: reducing array capacity truncated occupied elements\n"
            "<2, 3>\n3\n",
            output,
        )

    def test_ordered_set_retains_duplicates_and_runic_method_aliases(self):
        output = self.run_program(
            '''
            set(int) values = (3, 3, 4);
            print(values.ᛚᛖᛝᚦ());
            print(values.ᚠᛠᚾᛞ_ᚾᚦ(3, 2));
            print(values);
            '''
        )
        self.assertEqual("3\n1\n(3, 3, 4)\n", output)

    def test_struct_defaults_fields_and_instance_methods(self):
        output = self.run_program(
            '''
            struct Person {
                str name;
                int age = 18;

                nil birthday(Person self) {
                    self.age += 1;
                }
            }
            Person person = { name = "Ada"; };
            person.birthday();
            print(person.name);
            print(person.age);
            '''
        )
        self.assertEqual("Ada\n19\n", output)

    def test_struct_constructor_copy_resemblance_and_identity(self):
        output = self.run_program(
            '''
            struct Person {
                str name;
                int age = 18;
            }
            Person original = Person.new("Ada");
            Person alias = original;
            Person copied = original.copy();
            print(original == alias);
            print(original == copied);
            print(original.resembles(copied));
            copied.age = 20;
            print(original.resembles(copied));
            '''
        )
        self.assertEqual("true\nfalse\ntrue\nfalse\n", output)

    def test_enum_members_qualified_names_and_raw_values(self):
        output = self.run_program(
            '''
            enum(int) State = (
                READY = 2;
                RUNNING;
                DONE
            )
            State first = READY;
            State second = State.RUNNING;
            State third = 4;
            print(first);
            print(second);
            print(third);
            '''
        )
        self.assertEqual("State.READY\nState.RUNNING\nState.DONE\n", output)

    def test_verification_builtins_and_foreach_index(self):
        output = self.run_program(
            '''
            list(int) values = [4, 5];
            foreach (value in values) {
                print(index(value), end = "");
            }
            print(is_list(values));
            print(is_empty(values));
            arr(int, 2) array = <1, 2>;
            print(is_full(array));
            print(ᛁᛋ_ᚪᚱ(array));
            '''
        )
        self.assertEqual("01true\nfalse\ntrue\ntrue\n", output)

    def test_function_scope_hoisting_repeated_declarations_and_new(self):
        output = self.run_program(
            '''
            int count = 0;
            until (count == 3) {
                int latest = count;
                count += 1;
            }
            print(latest);
            new str count = "redeclared";
            print(count);
            '''
        )
        self.assertEqual("2\nredeclared\n", output)

    def test_contextual_types_survive_reassignment_and_nested_collections(self):
        output = self.run_program(
            '''
            struct Person { str name; }
            Person person = { name = "Ada"; };
            person = { name = "Grace"; };

            list(Person) people = [{ name = "Lin"; }];
            people[0] = { name = "Margaret"; };

            print(person.name);
            print(people[0].name);
            '''
        )
        self.assertEqual("Grace\nMargaret\n", output)

    def test_integer_methods_ascii_and_runic(self):
        output = self.run_program(
            '''
            print(5.gt(3));
            print(5.lt(3));
            print(5.between(5, 6));
            print(5.between("5", 6));
            print(5.ᛒᛁᛏᚹᛁᛁᚾ(1, "6"));
            '''
        )
        self.assertEqual("true\nfalse\ntrue\nfalse\ntrue\n", output)

    def test_mutating_conversions_change_and_narrow_variables(self):
        output = self.run_program(
            '''
            any number = "41";
            to_int(number);
            print(number + 1);

            any word = 123;
            ᛏᚣ_ᛋᛏᚱ(word);
            print(c"value: {word}");

            any letters = "abc";
            to_list(letters);
            print(letters);

            any fixed = [1, 2, 3];
            to_arr(fixed, 5);
            print(fixed);
            print(is_full(fixed));
            '''
        )
        self.assertEqual(
            "42\nvalue: 123\n[a, b, c]\n<1, 2, 3>\nfalse\n",
            output,
        )


class CommandLineTests(unittest.TestCase):
    def test_lowercase_thorn_is_a_source_extension(self):
        self.assertIn(thorn_source_path("hello.þ").suffix, SOURCE_SUFFIXES)

    def test_typable_thorn_is_a_source_extension(self):
        self.assertIn(thorn_source_path("hello.thorn").suffix, SOURCE_SUFFIXES)

    def test_other_source_extensions_are_rejected(self):
        with self.assertRaises(Exception) as context:
            thorn_source_path("hello.txt")
        self.assertIn(".þ", str(context.exception))
        self.assertIn(".thorn", str(context.exception))


class ExampleProgramTests(unittest.TestCase):
    def test_todo_app_adds_lists_removes_and_quits(self):
        source = (
            Path(__file__).parent / "examples" / "todo.thorn"
        ).read_text(encoding="utf-8")
        answers = iter([
            "1", "Buy milk",
            "1", "Write Thorn",
            "2",
            "3", "1",
            "2",
            "4",
        ])
        output = []

        run_source(
            source,
            output=output.append,
            input_function=lambda prompt: next(answers),
        )

        rendered = "".join(output)
        self.assertIn("Added: Buy milk\n", rendered)
        self.assertIn("1. Buy milk\n2. Write Thorn\n", rendered)
        self.assertIn("Completed: Buy milk\n", rendered)
        self.assertIn("Your tasks:\n1. Write Thorn\n", rendered)
        self.assertTrue(rendered.endswith("Farewell!\n"))


class RuntimeObjectTests(unittest.TestCase):
    def test_deep_copy_preserves_cycles_and_shared_references(self):
        shared = ThornList([1])
        original = ThornList()
        original.values.extend([shared, shared, original])

        copied = copy.deepcopy(original)

        self.assertIsNot(copied, original)
        self.assertIs(copied.values[0], copied.values[1])
        self.assertIs(copied, copied.values[2])
        self.assertIsNot(shared, copied.values[0])

    def test_runtime_errors_include_source_excerpt_and_thorn_call_stack(self):
        source = '''
float divide(int value) { return 10 / value; }
float wrapper() { return divide(0); }
wrapper();
'''
        with self.assertRaises(ThornRuntimeError) as context:
            run_source(source)

        rendered = format_runtime_error(context.exception, source, "errors.þ")
        self.assertIn("runtime error: division by zero", rendered)
        self.assertIn("--> errors.þ:2:", rendered)
        self.assertIn("^", rendered)
        self.assertIn("called from divide", rendered)
        self.assertIn("called from wrapper", rendered)


class FileIOTests(unittest.TestCase):
    def test_ascii_file_api_reads_writes_seeks_and_reports_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "notes.txt").as_posix()
            output = []
            run_source(
                f'''
                File file = open("{path}", "w+", encoding = "utf-8");
                print(file.writable());
                file.write("thorn\\n");
                file.flush();
                int position = file.tell();
                print(position.gt(0));
                file.seek(0);
                print(file.read(), end = "");
                print(file.closed());
                file.close();
                print(file.closed());
                ''',
                output=output.append,
            )
            self.assertEqual("true\ntrue\nthorn\nfalse\ntrue\n", "".join(output))
            self.assertEqual("thorn\n", Path(path).read_text(encoding="utf-8"))

    def test_runic_file_api_and_named_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "runes.txt").as_posix()
            output = []
            run_source(
                f'''
                ᚠᛠᛚ file = ᚩᛈᛖᚾ(
                    ᛈᚫᚦ = "{path}",
                    ᛗᚩᛞ = "w+",
                    ᛖᚾᚳᚩᛞᛁᛝ = "utf-8"
                );
                file.ᚹᚱᛠᛏ(ᚳᚪᚾᛏᛖᚾᛏ = "ᚦorn");
                file.ᛋᛁᛁᚳ(ᚢᚠᛋᛖᛏ = 0, ᚩᚱᛁᚷᚻᛁᚾ = 0);
                ᛈᚱᛁᚾᛏ(file.ᚱᛁᛁᛞ());
                file.ᚳᛚᚩᛋ();
                ᛈᚱᛁᚾᛏ(file.ᚳᛚᚩᛋᛞ());
                ''',
                output=output.append,
            )
            self.assertEqual("ᚦorn\ntrue\n", "".join(output))

    def test_closed_file_and_binary_mode_fail_as_thorn_runtime_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "closed.txt").as_posix()
            with self.assertRaises(ThornRuntimeError) as closed:
                run_source(
                    f'''
                    File file = open("{path}", "w+");
                    file.close();
                    file.read();
                    '''
                )
            self.assertIn("cannot read file", closed.exception.message)

            with self.assertRaises(ThornRuntimeError) as binary:
                run_source(f'File file = open("{path}", "rb");')
            self.assertIn("bytes type", binary.exception.message)


class PythonInteropTests(unittest.TestCase):
    def test_runic_pyimport_type_builtin_and_named_parameter(self):
        output = []
        run_source(
            '''
            ᛈᛠᚪᛒᚷᚻᛖᚳᛏ math = ᛈᛠᛁᛗᛈᛟᚱᛏ(
                ᛗᚫᚷᚻᚣᛚ = "math"
            );
            ᛈᚱᛁᚾᛏ(ᚠᛚᚩᛏ(math.sqrt(49)));
            ''',
            output=output.append,
        )
        self.assertEqual("7.0\n", "".join(output))

    def test_runic_struct_builtin_methods_and_named_other(self):
        output = []
        run_source(
            '''
            ᛋᛏᚱᚢᚳᛏ Pair { ᛁᚾᛏ value; }
            Pair left = Pair.ᚾᛁᚢ(3);
            Pair right = left.ᚳᚪᛈᛁᛁ();
            ᛈᚱᛁᚾᛏ(left.ᚱᛁᛋᛖᛗᛒᚢᛚ(ᚢᚦᚢ = right));
            ''',
            output=output.append,
        )
        self.assertEqual("true\n", "".join(output))

    def test_import_members_calls_named_arguments_and_conversions(self):
        output = []
        run_source(
            '''
            pyobject math = pyimport("math");
            float root = float(math.sqrt(81.0));
            float pi = float(math.pi);

            pyobject json = pyimport("json");
            pyobject encoded = json.dumps([1, 2], indent = 2);

            print(root);
            print(pi > 3.0);
            print(str(encoded));
            ''',
            output=output.append,
        )
        rendered = "".join(output)
        self.assertTrue(rendered.startswith("9.0\ntrue\n"))
        self.assertIn("[\n  1,\n  2\n]\n", rendered)

    def test_python_classes_and_direct_foreign_callables(self):
        with tempfile.TemporaryDirectory() as directory:
            path = (Path(directory) / "created.txt").as_posix()
            output = []
            run_source(
                f'''
                pyobject pathlib = pyimport("pathlib");
                pyobject constructor = pathlib.Path;
                pyobject path = constructor("{path}");
                path.write_text("hello", encoding = "utf-8");
                print(bool(path.exists()));
                print(str(path.read_text(encoding = "utf-8")));
                ''',
                output=output.append,
            )
            self.assertEqual("true\nhello\n", "".join(output))

    def test_python_index_slice_iteration_and_collection_conversion(self):
        output = []
        run_source(
            '''
            pyobject json = pyimport("json");
            pyobject values = json.loads("[10, 20, 30]");

            print(int(values[1]));
            print(str(values[0:2]));

            foreach (value in values) {
                print(int(value), end = " ");
            }
            print("");

            to_list(values);
            print(values);
            ''',
            output=output.append,
        )
        self.assertEqual(
            "20\n[10, 20]\n10 20 30 \n[10, 20, 30]\n",
            "".join(output),
        )

    def test_python_exceptions_become_thorn_runtime_errors(self):
        with self.assertRaises(ThornRuntimeError) as domain:
            run_source(
                '''
                pyobject math = pyimport("math");
                math.sqrt(-1);
                '''
            )
        self.assertIn("Python ValueError: math domain error", domain.exception.message)

        with self.assertRaises(ThornRuntimeError) as missing:
            run_source('pyobject module = pyimport("thorn_module_that_does_not_exist");')
        self.assertIn("Python ModuleNotFoundError", missing.exception.message)


if __name__ == "__main__":
    unittest.main()
