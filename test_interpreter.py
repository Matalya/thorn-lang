import unittest
from pathlib import Path

from thorn import SOURCE_SUFFIXES, thorn_source_path, run_source


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


if __name__ == "__main__":
    unittest.main()
