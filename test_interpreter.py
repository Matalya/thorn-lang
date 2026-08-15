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

    def test_break_and_continue_across_all_loop_forms(self):
        output = self.run_program(
            '''
            int count = 0;
            while (count < 6) {
                count += 1;
                if (count == 2) { continue; }
                if (count == 5) { break; }
                print(count, end = "");
            }
            print("|", end = "");

            int untilCount = 0;
            until (untilCount >= 5) {
                untilCount += 1;
                if (untilCount == 2) { continue; }
                if (untilCount == 4) { break; }
                print(untilCount, end = "");
            }
            print("|", end = "");

            for (number from 0 to 6) {
                if (number == 1) { continue; }
                if (number == 4) { break; }
                print(number, end = "");
            }
            print("|", end = "");

            foreach (number in [1, 2, 3, 4, 5]) {
                if (number == 2) { continue; }
                if (number == 4) { break; }
                print(number, end = "");
            }
            '''
        )
        self.assertEqual("134|13|023|13", output)

    def test_break_targets_the_nearest_nested_loop(self):
        output = self.run_program(
            '''
            for (outer from 0 to 3) {
                for (inner from 0 to 4) {
                    if (inner == 1) { continue; }
                    if (inner == 3) { break; }
                    print(c"{outer}{inner},", end = "");
                }
            }
            '''
        )
        self.assertEqual("00,02,10,12,20,22,", output)

    def test_runic_break_and_continue(self):
        output = self.run_program(
            '''
            ᚠᛟ (number ᚠᚱᛟᛗ 0 ᛏᚣ 6) {
                ᛁᚠ (number == 1) { ᚳᚢᚾᛏᛁᚾᛄᚣ; }
                ᛁᚠ (number == 4) { ᛒᚱᛠᚳ; }
                print(number, end = "");
            }
            '''
        )
        self.assertEqual("023", output)

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

    def test_heterogeneous_array_runtime_schema_and_prefix_growth(self):
        output = self.run_program(
            '''
            arr(int, str * 2, bool) data = <10, "hello">;
            print(data.length());
            print(data.capacity());
            data[2] = "hi";
            data.append(true);
            data[0] = 20;
            print(data);

            arr(str * 2, bool) tail = data[1:];
            print(tail);

            arr(int, str) empty;
            print(empty.length());
            print(empty.capacity());

            arr(int, str) make_pair(int value, str label) {
                return <value, label>;
            }
            arr(int, str) pair = make_pair(7, "seven");
            print(pair);

            struct Person { str name; }
            Person ada = Person.new("Ada");
            arr(Person * 2, int) party = <ada>;
            print(party[0].name);
            '''
        )

        self.assertEqual(
            "2\n4\n<20, hello, hi, true>\n<hello, hi, true>\n"
            "0\n2\n<7, seven>\nAda\n",
            output,
        )

    def test_heterogeneous_array_runtime_rejects_uninitialized_gaps_and_dynamic_mismatch(self):
        with self.assertRaises(ThornRuntimeError) as uninitialized:
            self.run_program(
                '''
                arr(int, str, bool) data = <10, "hello">;
                print(data[2]);
                '''
            )
        self.assertIn("slot 2 is uninitialized", str(uninitialized.exception))

        with self.assertRaises(ThornRuntimeError) as gap:
            self.run_program(
                '''
                arr(int, str, bool) data = <10>;
                data[2] = true;
                '''
            )
        self.assertIn("cannot contain gaps", str(gap.exception))

        with self.assertRaises(ThornRuntimeError) as dynamicMismatch:
            self.run_program(
                '''
                arr(int, str, bool) data = <10, "hello">;
                int position = 2;
                data[position] = "true";
                '''
            )
        self.assertIn("does not match type 'bool'", str(dynamicMismatch.exception))

        with self.assertRaises(ThornRuntimeError) as appendMismatch:
            self.run_program(
                '''
                arr(int, str) data;
                data.append(10);
                data.append(20);
                '''
            )
        self.assertIn("does not match type 'str'", str(appendMismatch.exception))

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

    def test_string_length_ascii_and_runic(self):
        output = self.run_program(
            '''
            str text = "Futhorc";
            print(text.length());
            print("ᚠᚢᚦᚩᚱᚳ".ᛚᛖᛝᚦ());
            '''
        )
        self.assertEqual("7\n6\n", output)

    def test_string_manipulation_methods(self):
        output = self.run_program(
            '''
            str original = "  Hello, MANXA world!  ";
            print(original.lower());
            print(original.upper());
            print(original.strip());
            print("...thorn...".strip("."));
            print("one  two\\nthree".split());
            print("a--b--c".split("--"));
            print("hello".replace("hell", "potat"));
            print("one one one".replace("one", "two", count = 2));
            print(original.contains("MANXA"));
            print(original.contains("mana"));
            print(original);
            '''
        )
        self.assertEqual(
            (
                "  hello, manxa world!  \n"
                "  HELLO, MANXA WORLD!  \n"
                "Hello, MANXA world!\n"
                "thorn\n"
                "[one, two, three]\n"
                "[a, b, c]\n"
                "potato\n"
                "two two one\n"
                "true\n"
                "false\n"
                "  Hello, MANXA world!  \n"
            ),
            output
        )

    def test_string_case_methods_are_unicode_aware(self):
        output = self.run_program(
            '''
            print("ÁRVORE ÑANDÚ".lower());
            print("árvore ñandú".upper());
            '''
        )
        self.assertEqual("árvore ñandú\nÁRVORE ÑANDÚ\n", output)

    def test_string_search_and_text_collection_join_methods(self):
        output = self.run_program(
            '''
            str text = "Futhorc language";
            print(text.starts_with("Futh"));
            print(text.ends_with("age"));
            print(text.find("orc"));
            print(text.find("Python"));
            print("aaaaa".count("aa"));

            list(str) words = ["The", "Thorn", "Language"];
            list(char) letters = ['r', 'u', 'n', 'e'];
            list(str | char) mixed = ["Futh", 'o', "rc"];
            arr(str, 3) names = <"Iljeri", "Ciwa", "Emijl">;
            set(char) marks = ('!', '?', '!');
            list(str) empty = [];
            print(words.join(" "));
            print(letters.join());
            print(mixed.join());
            print(names.join(" / "));
            print(marks.join());
            print(c"<{empty.join()}>");
            '''
        )
        self.assertEqual(
            (
                "true\n"
                "true\n"
                "4\n"
                "nil\n"
                "2\n"
                "The Thorn Language\n"
                "rune\n"
                "Futhorc\n"
                "Iljeri / Ciwa / Emijl\n"
                "!?!\n"
                "<>\n"
            ),
            output
        )

    def test_composite_strings_decode_escapes_in_literal_components(self):
        output = self.run_program(
            r'''
            str letter = "a";
            print(c"\r\x1b[2K{letter}", end = "");
            print(c"\nLiteral: \{letter\}");
            '''
        )
        self.assertEqual("\r\x1b[2Ka\nLiteral: {letter}\n", output)

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

    def test_non_mutating_collection_conversions(self):
        output = self.run_program(
            '''
            list(int) original = [1, 2];
            list(int) copied = list(int, original);
            copied.append(3);

            list(char) letters = list(char, "abc");
            arr(int, 4) fixed = arr(int, original, capacity = 4);
            set(int) ordered = set(int, [2, 1, 2]);
            list(list(int)) nested = [[1]];
            list(list(int)) outerCopy = list(list(int), nested);
            outerCopy[0].append(2);

            print(original);
            print(copied);
            print(letters);
            print(fixed);
            print(fixed.capacity());
            print(ordered);
            print(nested);
            '''
        )
        self.assertEqual(
            "[1, 2]\n[1, 2, 3]\n[a, b, c]\n<1, 2>\n4\n"
            "(2, 1, 2)\n[[1, 2]]\n",
            output,
        )

    def test_collection_conversion_defaults_truncation_and_python_iterable(self):
        output = self.run_program(
            '''
            list(int) emptyList = list(int);
            arr(int, 0) emptyArray = arr(int);
            arr(int, 3) reserved = arr(int, capacity = 3);
            set(int) emptySet = set(int);

            arr(int, 2) truncated = arr(int, [1, 2, 3], 2);

            import python "builtins" as builtins;
            pyobject numbers = builtins.range(1, 4);
            list(int) fromPython = list(int, numbers);

            print(emptyList);
            print(emptyArray);
            print(reserved.capacity());
            print(emptySet);
            print(truncated);
            print(fromPython);
            '''
        )
        self.assertEqual(
            "warning: array initializer was truncated to fit its capacity\n"
            "[]\n<>\n3\n()\n<1, 2>\n[1, 2, 3]\n",
            output,
        )

    def test_runic_non_mutating_collection_conversions(self):
        output = self.run_program(
            '''
            ᛚᛁᛋᛏ(ᛁᚾᛏ) values = ᛚᛁᛋᛏ(ᛁᚾᛏ, [1, 2]);
            ᚪᚱ(ᛁᚾᛏ, 3) fixed = ᚪᚱ(ᛁᚾᛏ, values, 3);
            ᛋᛖᛏ(ᛁᚾᛏ) ordered = ᛋᛖᛏ(ᛁᚾᛏ, values);
            ᛈᚱᛁᚾᛏ(values);
            ᛈᚱᛁᚾᛏ(fixed);
            ᛈᚱᛁᚾᛏ(ordered);
            '''
        )
        self.assertEqual("[1, 2]\n<1, 2>\n(1, 2)\n", output)

    def test_collection_conversion_rejects_dynamic_element_type_mismatch(self):
        with self.assertRaises(ThornRuntimeError) as context:
            run_source('list(int) values = list(int, ["wrong"]);')
        self.assertIn("does not match type 'int'", context.exception.message)

        with self.assertRaises(ThornRuntimeError) as nested:
            run_source(
                'list(list(int)) values = list(list(int), [["wrong"]]);'
            )
        self.assertIn("does not match type 'int'", nested.exception.message)


class CommandLineTests(unittest.TestCase):
    def test_thorn_character_is_a_source_extension(self):
        self.assertIn(thorn_source_path("hello.þ").suffix, SOURCE_SUFFIXES)

    def test_typable_futhorc_is_a_source_extension(self):
        self.assertIn(thorn_source_path("hello.futhorc").suffix, SOURCE_SUFFIXES)

    def test_other_source_extensions_are_rejected(self):
        with self.assertRaises(Exception) as context:
            thorn_source_path("hello.txt")
        self.assertIn(".þ", str(context.exception))
        self.assertIn(".futhorc", str(context.exception))


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
                print(file);
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
            self.assertEqual(
                f"File {{ path = {path}, mode = w+, closed = false }}\n"
                "true\ntrue\nthorn\nfalse\ntrue\n",
                "".join(output),
            )
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


class DictionaryTests(unittest.TestCase):
    def run_program(self, source):
        output = []
        run_source(source, output=output.append)
        return "".join(output)

    def test_typed_literals_indexing_assignment_and_methods(self):
        output = self.run_program(
            '''
            dict(str | int, int) scores = {
                "Ada" -> 10;
                "Grace" -> 20;
                3 -> 30
            };
            scores["Ada"] += 5;
            scores["Linus"] = 40;
            print(scores["Ada"]);
            print(scores.get("missing", 99));
            print(scores.has(3));
            print(scores.keys());
            print(scores.values());
            print(scores.items());
            print(scores.remove("Grace"));
            print(scores.length());
            foreach (key in scores) { print(key); }
            '''
        )
        self.assertEqual(
            (
                "15\n99\ntrue\n[Ada, Grace, 3, Linus]\n"
                "[15, 20, 30, 40]\n"
                "[<Ada, 15>, <Grace, 20>, <3, 30>, <Linus, 40>]\n"
                "20\n3\nAda\n3\nLinus\n"
            ),
            output,
        )

    def test_runic_dictionary_type_and_method_aliases(self):
        output = self.run_program(
            '''
            ᛞᛁᚳᛏ(ᛋᛏᚱ, ᛁᚾᛏ) scores = {
                "Ada" -> 10;
                "Grace" -> 20
            };
            print(scores.ᛚᛖᛝᚦ());
            print(scores.ᚷᛖᛏ("Ada"));
            print(scores.ᚻᚫᛋ("Grace"));
            print(scores.ᚳᛁᛁᛋ());
            print(scores.ᚠᚫᛚᛄᚣᛋ());
            print(scores.ᛠᛏᛖᛗᛋ());
            ᛞᛁᚳᛏ(ᛋᛏᚱ, ᛁᚾᛏ) copied = scores.ᚳᚪᛈᛁ();
            print(scores.ᚱᛁᛗᚣᚠ("Ada"));
            scores.ᚳᛚᛁᚢᚱ();
            print(scores.ᛚᛖᛝᚦ());
            print(copied.ᛚᛖᛝᚦ());
            '''
        )
        self.assertEqual(
            "2\n10\ntrue\n[Ada, Grace]\n[10, 20]\n"
            "[<Ada, 10>, <Grace, 20>]\n10\n0\n2\n",
            output,
        )

    def test_empty_const_copy_clear_and_distinct_python_numeric_keys(self):
        output = self.run_program(
            '''
            const dict(any, str) values = {};
            values[true] = "bool";
            values[1] = "int";
            values[1.0] = "float";
            dict(any, str) copied = values.copy();
            values.clear();
            print(values.length());
            print(copied.length());
            print(copied[true]);
            print(copied[1]);
            print(copied[1.0]);
            print(is_dict(copied));
            dict(str, int) first = {"a" -> 1; "b" -> 2;};
            dict(str, int) second = {"b" -> 2; "a" -> 1;};
            print(first == second);
            '''
        )
        self.assertEqual("0\n3\nbool\nint\nfloat\ntrue\ntrue\n", output)

    def test_python_conversion_rejects_colliding_futhorc_keys(self):
        with self.assertRaises(ThornRuntimeError) as context:
            run_source(
                '''
                dict(any, str) values = {
                    true -> "bool";
                    1 -> "int";
                };
                pyobject builtins = pyimport("builtins");
                builtins.dict(values);
                '''
            )
        self.assertIn("collide under Python equality", context.exception.message)

    def test_python_dictionary_conversion_in_both_directions(self):
        output = self.run_program(
            '''
            pyobject builtins = pyimport("builtins");
            dict(str, int) native = dict(
                str,
                int,
                builtins.dict(apples = 2, pears = 3)
            );
            print(native);
            pyobject foreign = builtins.dict(native);
            print(str(foreign));
            native["apples"] = 9;
            print(str(foreign));
            '''
        )
        self.assertEqual(
            "{apples -> 2; pears -> 3}\n"
            "{'apples': 2, 'pears': 3}\n"
            "{'apples': 2, 'pears': 3}\n",
            output,
        )

    def test_dynamic_unhashable_key_is_a_runtime_error(self):
        with self.assertRaises(ThornRuntimeError) as context:
            run_source(
                '''
                dict(any, int) values = {};
                pyobject builtins = pyimport("builtins");
                pyobject key = builtins.list([1, 2]);
                values[key] = 1;
                '''
            )
        self.assertIn("not hashable", context.exception.message)

        with self.assertRaises(ThornRuntimeError) as native:
            run_source(
                '''
                dict(any, int) values = {};
                any key = [1, 2];
                values[key] = 1;
                '''
            )
        self.assertIn("not hashable", native.exception.message)


class PythonInteropTests(unittest.TestCase):
    def test_native_python_import_ascii_and_runic(self):
        output = []
        run_source(
            '''
            import python "math" as math;
            ᛁᛗᛈᛟᚱᛏ ᛈᛠᚦᚣᚾ "statistics" ᚫᛋ stats;

            print(float(math.sqrt(64)));
            print(float(stats.mean([2.0, 4.0, 6.0])));
            ''',
            output=output.append,
        )
        self.assertEqual("8.0\n4.0\n", "".join(output))

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


class NativeModuleTests(unittest.TestCase):
    def run_module_program(self, directory, source, name="main.futhorc"):
        path = Path(directory) / name
        path.write_text(source, encoding="utf-8")
        output = []
        run_source(
            source,
            source_path=path,
            output=output.append,
        )
        return "".join(output)

    def test_module_import_alias_from_import_and_single_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "numbers.futhorc").write_text(
                '''
                print("numbers initialized");
                int answer = 42;
                int add(int left, int right) { return left + right; }
                ''',
                encoding="utf-8",
            )
            output = self.run_module_program(
                root,
                '''
                import numbers;
                import numbers as nums;
                from numbers import add as sum;
                from numbers import answer;
                ᚠᚱᛟᛗ numbers ᛁᛗᛈᛟᚱᛏ answer ᚫᛋ runicAnswer;
                print(numbers.answer);
                print(nums.add(2, 3));
                print(sum(answer, 1));
                print(runicAnswer);
                ''',
            )
            self.assertEqual("numbers initialized\n42\n5\n43\n42\n", output)

    def test_imported_nominal_struct_and_enum_type_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "people.futhorc").write_text(
                '''
                struct Person {
                    str name;
                    str greet(Person self) { return c"Hello, {self.name}"; }
                }
                enum(str) Role = (
                    WRITER = "writer";
                    EDITOR = "editor"
                )
                Person make_person(str name) { return Person.new(name); }
                ''',
                encoding="utf-8",
            )
            output = self.run_module_program(
                root,
                '''
                import people;
                from people import Person as Human;
                from people import Role as Job;
                from people import make_person as make;
                Human ada = make("Ada");
                Human grace = Human.new("Grace");
                Job role = people.WRITER;
                print(ada.greet());
                print(grace.name);
                print(people.make_person("Lin").name);
                print(role);
                ''',
            )
            self.assertEqual("Hello, Ada\nGrace\nLin\nRole.WRITER\n", output)

    def test_dotted_module_names_are_rejected_as_member_syntax(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SyntaxError) as dotted:
                self.run_module_program(directory, "import world.people;")
            self.assertIn(
                "use 'from module import member;'",
                str(dotted.exception),
            )

            with self.assertRaises(SyntaxError) as dottedFrom:
                self.run_module_program(
                    directory,
                    "from world.people import Person;",
                )
            self.assertIn(
                "module names must be single identifiers",
                str(dottedFrom.exception),
            )

    def test_imported_function_arguments_remain_statically_typed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "maths.futhorc").write_text(
                "int twice(int value) { return value * 2; }",
                encoding="utf-8",
            )
            source = 'import maths;\nmaths.twice("bad");'
            with self.assertRaises(SyntaxError) as caught:
                self.run_module_program(root, source)
            self.assertIn("must have type 'int', got 'str'", str(caught.exception))

    def test_missing_module_export_and_circular_import_are_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "empty.futhorc").write_text("int present = 1;", encoding="utf-8")
            with self.assertRaises(SyntaxError) as missingExport:
                self.run_module_program(root, "from empty import absent;")
            self.assertIn("has no exported name 'absent'", str(missingExport.exception))

            (root / "a.futhorc").write_text("import b;", encoding="utf-8")
            (root / "b.futhorc").write_text("import a;", encoding="utf-8")
            with self.assertRaises(SyntaxError) as circular:
                self.run_module_program(root, "import a;")
            self.assertIn("Circular module import detected", str(circular.exception))

    def test_missing_module_and_pathless_source_are_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SyntaxError) as missing:
                self.run_module_program(directory, "import nowhere;")
            self.assertIn("Module 'nowhere' was not found", str(missing.exception))

        with self.assertRaises(SyntaxError) as pathless:
            run_source("import nowhere;")
        self.assertIn("without a file path", str(pathless.exception))


if __name__ == "__main__":
    unittest.main()
