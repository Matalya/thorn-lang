import unittest

from lexer import Lexer
from parser import Parser, TokenError, TokenStream
from semantic import SemanticAnalyzer
from Token import TokenKind as TK
from th_ast import (
    EnumDeclaration,
    FunctionCall,
    Identifier,
    Literal,
    NamedArgument,
    NamedTypeDeclaration,
    StructDeclaration,
    StructLiteral,
    Uninitialized
)


def analyze(source: str):
    lexer = Lexer(source)
    lexer.Tokenize()

    tokens = [
        token
        for token in lexer.tokenStream
        if token.kind != TK.COMMENT
    ]

    program = Parser(TokenStream(tokens, source=source)).parse()
    return SemanticAnalyzer().analyze(program)


def parseProgram(source: str):
    lexer = Lexer(source)
    lexer.Tokenize()

    tokens = [
        token
        for token in lexer.tokenStream
        if token.kind != TK.COMMENT
    ]

    return Parser(TokenStream(tokens, source=source)).parse()


class MissingSemicolonDiagnosticTests(unittest.TestCase):
    def assertMissingSemicolon(
        self,
        source: str,
        context: str,
        line: int
    ):
        with self.assertRaises(TokenError) as caught:
            parseProgram(source)

        message = str(caught.exception)
        self.assertIn(
            f"Missing semicolon after {context} at line {line},",
            message
        )
        self.assertIn("^ add ';' here", message)

    def test_variable_declaration_points_to_previous_line(self):
        self.assertMissingSemicolon(
            'int count = 0\nprint(count);',
            "variable declaration",
            1
        )

    def test_uninitialized_declaration_recovers_as_declaration(self):
        self.assertMissingSemicolon(
            'int count\nprint(count);',
            "variable declaration",
            1
        )

    def test_statement_kinds_name_the_missing_terminator_context(self):
        cases = (
            ('int count = 0;\ncount = 1\nprint(count);', "assignment", 2),
            ('print("one")\nprint("two");', "expression statement", 1),
            ('int value() {\nreturn 1\n}', "return statement", 2),
            ('nil done() {\nreturn\n}', "return statement", 2),
            ('while (true) {\nbreak\n}', "break statement", 2),
            ('while (true) {\ncontinue\n}', "continue statement", 2),
            (
                'import python "sys" as sys\nprint(sys);',
                "Python import",
                1
            ),
            (
                'struct Point {\nint x\n}',
                "struct field declaration",
                2
            ),
            (
                'dict(str, int) values = {"one" -> 1\n"two" -> 2};',
                "dictionary entry",
                1
            ),
        )

        for source, context, line in cases:
            with self.subTest(context=context):
                self.assertMissingSemicolon(source, context, line)

    def test_diagnostic_includes_source_line_and_column(self):
        with self.assertRaises(TokenError) as caught:
            parseProgram("int count = 0\nprint(count);")

        self.assertEqual(
            "Missing semicolon after variable declaration at line 1, "
            "column 14.\n"
            "1 | int count = 0\n"
            "  |              ^ add ';' here",
            str(caught.exception)
        )


class CompoundAssignmentTests(unittest.TestCase):
    def test_valid_numeric_compound_assignments(self):
        issues = analyze(
            """
            int count = 5;
            count += 2;
            count -= 1;
            count *= 3;
            count %= 4;
            count //= 2;

            float ratio = 1.5;
            ratio += 2;
            ratio /= 2;

            int | float flexible = 1;
            flexible += 2;
            """
        )

        self.assertEqual([], issues)

    def test_invalid_operand_types(self):
        issues = analyze(
            """
            int count = 5;
            count += "hello";

            bool enabled = true;
            enabled += false;

            any unknown = 1;
            unknown += 2;

            str | int flexible = 1;
            flexible += 2;
            """
        )

        self.assertEqual(4, len(issues))
        self.assertTrue(all(
            issue.message.startswith("Operator '+' cannot be applied")
            for issue in issues
        ))

    def test_compound_result_must_fit_target(self):
        issues = analyze(
            """
            int count = 5;
            count /= 2;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "Compound assignment '/=' produces a value of type 'float'",
            issues[0].message
        )


class OperatorExpressionTests(unittest.TestCase):
    def test_valid_operator_expressions(self):
        issues = analyze(
            """
            int arithmetic = 1 + 2 * 3;
            float division = 5 / 2;
            bool logic = true and not false;
            bool comparison = 1.0 >= 1;
            bool equality = "thorn" == "thorn";
            """
        )

        self.assertEqual([], issues)

    def test_invalid_operator_expressions(self):
        issues = analyze(
            """
            int arithmetic = 1 + "two";
            bool logic = 1 and true;
            bool negation = not 1;
            int division = 5 / 2;
            """
        )

        self.assertEqual(4, len(issues))
        self.assertIn("Operator '+' cannot be applied", issues[0].message)
        self.assertIn("Operator 'and' cannot be applied", issues[1].message)
        self.assertIn("Operator 'not' cannot be applied", issues[2].message)
        self.assertIn("Cannot initialize variable 'division'", issues[3].message)


class ContextualExpressionTests(unittest.TestCase):
    def test_valid_conditions_and_for_bounds(self):
        issues = analyze(
            """
            if (true) {
            } elsif (1 < 2) {
            }

            while (false or true) {
            }

            until (not false) {
            }

            for (i from 0 to 10) {
            }
            """
        )

        self.assertEqual([], issues)

    def test_invalid_conditions_and_for_bounds(self):
        issues = analyze(
            """
            if (1) {
            } elsif ("yes") {
            }

            while (1.5) {
            }

            until (nil) {
            }

            for (i from 0.0 to 10) {
            }

            for (j from 0 to 5.5) {
            }
            """
        )

        self.assertEqual(6, len(issues))
        self.assertTrue(issues[0].message.startswith("If condition must"))
        self.assertTrue(issues[1].message.startswith("Elsif condition must"))
        self.assertTrue(issues[2].message.startswith("While condition must"))
        self.assertTrue(issues[3].message.startswith("Until condition must"))
        self.assertTrue(issues[4].message.startswith("For-loop start must"))
        self.assertTrue(issues[5].message.startswith("For-loop end must"))

    def test_failed_inference_does_not_add_context_noise(self):
        issues = analyze(
            """
            if (missing) {
            }

            while (1 + "two") {
            }
            """
        )

        self.assertEqual(2, len(issues))
        self.assertTrue(issues[0].message.startswith("Unknown identifier"))
        self.assertTrue(issues[1].message.startswith("Operator '+' cannot"))

    def test_break_and_continue_require_a_loop_in_the_same_callable(self):
        issues = analyze(
            '''
            break;
            continue;

            while (true) {
                break;
                continue;

                nil nested() {
                    break;
                    continue;
                }
            }
            '''
        )

        self.assertEqual(4, len(issues))
        self.assertEqual(
            [
                "Break statement cannot appear outside a loop.",
                "Continue statement cannot appear outside a loop.",
                "Break statement cannot appear outside a loop.",
                "Continue statement cannot appear outside a loop.",
            ],
            [issue.message for issue in issues],
        )


class CollectionSemanticTests(unittest.TestCase):
    def test_heterogeneous_array_schema_inference_and_positional_types(self):
        issues = analyze(
            '''
            struct Person { str name; }
            struct Person3 { str name; }
            Person ada = Person.new("Ada");
            Person3 numberedName = Person3.new("Grace");

            arr(int, str * 3) data = <10, "hello">;
            int number = data[0];
            str greeting = data[1];
            data[2] = "hi";

            int position = 1;
            int | str dynamic = data[position];

            arr(Person * 2, int) party = <ada>;
            Person first = party[0];

            arr(Person3, list(int) * 2) unambiguous = <numberedName>;
            Person3 retainedName = unambiguous[0];

            arr(int, str * 2, 3) explicit = <1, "two">;

            arr(int, str) make_pair(int value, str label) {
                return <value, label>;
            }
            arr(int, str) pair = make_pair(7, "seven");
            '''
        )

        self.assertEqual([], issues)

    def test_heterogeneous_array_rejects_wrong_positions_and_schema_mutation(self):
        issues = analyze(
            '''
            arr(int, str, bool) data = <10, "hello">;
            data[2] = "true";
            str wrong = data[0];
            data[3];
            data.prepend(5);
            arr(str, int, bool) reordered = data;
            '''
        )

        messages = [issue.message for issue in issues]
        self.assertTrue(any("indexed element" in message for message in messages))
        self.assertTrue(any("variable 'wrong'" in message for message in messages))
        self.assertTrue(any("outside its 3-slot schema" in message for message in messages))
        self.assertTrue(any("no method named 'prepend'" in message for message in messages))
        self.assertTrue(any("variable 'reordered'" in message for message in messages))

    def test_heterogeneous_array_schema_counts_are_validated_by_parser(self):
        invalid = (
            "arr(int, str, 3) data;",
            "arr(int * 0, str) data;",
            "arr(int) data;",
        )

        for source in invalid:
            with self.subTest(source=source):
                with self.assertRaises(TokenError):
                    parseProgram(source)

    def test_collection_inference_indexing_and_slicing(self):
        issues = analyze(
            """
            list(int) numbers = [1, 2, 3];
            int first = numbers[0];
            list(int) tail = numbers[1:];

            arr(str, 4) names = <"thorn", "briar">;
            str name = names[1];

            set(bool) flags = (true, false);
            bool flag = flags[0];

            list(int | str) mixed = [1, "two"];
            int | str item = mixed[0];

            list(int) emptyList = [];
            arr(str, 3) emptyArray = <>;
            set(bool) emptySet = ();
            """
        )

        self.assertEqual([], issues)

    def test_invalid_collection_elements_and_indices(self):
        issues = analyze(
            """
            list(int) numbers = [1, "two"];
            int badIndex = numbers["first"];

            int scalar = 1;
            int badTarget = scalar[0];

            list(int) badSlice = numbers[0.5:];
            arr(int, 2) tooMany = <1, 2, 3>;
            """
        )

        self.assertEqual(5, len(issues))
        self.assertIn("Cannot initialize variable 'numbers'", issues[0].message)
        self.assertIn("Collection index must have type 'int'", issues[1].message)
        self.assertIn("Cannot index a value of type 'int'", issues[2].message)
        self.assertIn("Slice start must have type 'int'", issues[3].message)
        self.assertIn("Cannot initialize variable 'tooMany'", issues[4].message)


class FunctionCallTests(unittest.TestCase):
    def test_parser_preserves_defaults_and_named_arguments(self):
        program = parseProgram(
            """
            str greet(str name, str punctuation = "!") {
                return name + punctuation;
            }

            greet(punctuation = "?", name = "Ada");
            """
        )
        declaration = program.statements[0]
        call = program.statements[1].expression

        self.assertIsInstance(
            declaration.parameters[1].defaultValue,
            Literal
        )
        self.assertIsInstance(call, FunctionCall)
        self.assertTrue(all(
            isinstance(argument, NamedArgument)
            for argument in call.arguments
        ))
        self.assertEqual(
            ["punctuation", "name"],
            [argument.name.name for argument in call.arguments]
        )

    def test_defaults_and_named_arguments_bind_function_parameters(self):
        issues = analyze(
            """
            struct Person { str name; }
            enum(int) State = ( READY = 0; DONE = 1; )

            str greet(
                str name,
                str greeting = "Hello",
                str punctuation = "!"
            ) {
                return c"{greeting}{name}{punctuation}";
            }

            Person identity(Person value = { name = "Ada"; }) {
                return value;
            }

            State chooseState(State value = 0) {
                return value;
            }

            str first = greet("Ada");
            str second = greet("Ada", "Hi", "?");
            str third = greet(
                punctuation = "?",
                name = "Grace"
            );
            Person defaultPerson = identity();
            Person namedPerson = identity(
                value = { name = "Lin"; }
            );
            State defaultState = chooseState();
            State namedState = chooseState(value = 1);

            print("hello", end = "");
            str preview = input(preview = "> ");
            int converted = int(value = "5");
            """
        )

        self.assertEqual([], issues)

    def test_invalid_defaults_and_named_argument_bindings_are_reported(self):
        issues = analyze(
            """
            int invalidDefault(int value = "bad") {
                return value;
            }

            int invalidOrder(int optional = 1, int required) {
                return required;
            }

            int laterReference(int first = second, int second = 2) {
                return first;
            }

            int combine(int left, int right = 2) {
                return left + right;
            }

            combine();
            combine(1, missing = 2);
            combine(left = 1, left = 2);
            combine(1, left = 2);
            combine(left = 1, 2);
            combine(right = "bad", left = 1);
            combine(1, 2, 3);
            """
        )

        self.assertEqual(10, len(issues))
        self.assertIn("Default value for parameter 'value'", issues[0].message)
        self.assertIn("Required parameter 'required'", issues[1].message)
        self.assertIn("Unknown identifier 'second'", issues[2].message)
        self.assertIn("missing required parameter", issues[3].message)
        self.assertIn("no parameter named 'missing'", issues[4].message)
        self.assertIn("provides parameter 'left' more than once", issues[5].message)
        self.assertIn("provides parameter 'left' more than once", issues[6].message)
        self.assertIn("Positional arguments cannot follow", issues[7].message)
        self.assertIn("must have type 'int', got 'str'", issues[8].message)
        self.assertIn("got 3", issues[9].message)

    def test_question_mark_is_not_optional_parameter_syntax(self):
        with self.assertRaises(TokenError):
            parseProgram(
                """
                int invalid(int ?value) {
                    return 0;
                }
                """
            )

    def test_calls_check_arguments_and_infer_return_types(self):
        issues = analyze(
            """
            int result = add(1, 2);

            int add(int left, int right) {
                return left + right;
            }

            list(int) echo(list(int) values) {
                return values;
            }

            list(int) copied = echo([1, 2]);
            """
        )

        self.assertEqual([], issues)

    def test_invalid_calls(self):
        issues = analyze(
            """
            int add(int left, int right) {
                return left + right;
            }

            add(1);
            add(1, "two");

            int value = 1;
            value();
            """
        )

        self.assertEqual(3, len(issues))
        self.assertIn("expects 2 argument(s), got 1", issues[0].message)
        self.assertIn("Argument 2", issues[1].message)
        self.assertIn("is not callable", issues[2].message)


class CollectionMethodSemanticTests(unittest.TestCase):
    def test_list_methods_check_arguments_and_infer_results(self):
        issues = analyze(
            """
            struct Person { str name; }
            enum(int) State = ( READY = 0; )

            list(int) numbers = [1, 2, 3];
            const list(int) constantNumbers = [1];
            list(Person) people = [];
            list(State) states = [];

            numbers.append(4);
            numbers.insert(item = 5, index = 1);
            numbers.prepend(0);
            int replaced = numbers.replace_at(item = 9, index = 0);
            list(int) shortened = numbers.shorten();
            list(int) shaved = numbers.shave(amount = 2);
            int removed = numbers.remove_at(index = 0);
            int size = numbers.length();
            int | nil first = numbers.find_first("anything");
            int | nil nth = numbers.find_nth(item = 2, number = 1);
            int | nil last = numbers.find_last(2);
            int located = numbers.locate(0);
            numbers.compress();
            list(int) copied = numbers.copy();

            constantNumbers.append(2);
            people.append({ name = "Ada"; });
            states.append(0);
            """
        )

        self.assertEqual([], issues)

    def test_array_and_set_methods_preserve_collection_types(self):
        issues = analyze(
            """
            arr(int, 5) values = <1, 2, 3>;
            values.resize(new_size = 8);
            int used = values.length();
            int room = values.capacity();
            values.append(4);
            values.insert(5, 1);
            values.prepend(0);
            int replaced = values.replace_at(9, 0);
            list(int) shortened = values.shorten();
            int removed = values.remove_at(0);
            list(int) shaved = values.shave();
            int | nil first = values.find_first(2);
            int | nil nth = values.find_nth(2, 1);
            int | nil last = values.find_last(2);
            int located = values.locate(index = 0);
            values.compress();
            arr(int, 5) copied = values.copy();
            values.fill(value = 9);
            values.skintight();
            values.shrink_to_fit();

            set(str) names = ("Ada", "Grace");
            int count = names.length();
            int | nil firstName = names.find_first("Ada");
            int | nil nthName = names.find_nth("Ada", 1);
            int | nil lastName = names.find_last("Ada");
            str name = names.locate(0);
            set(str) copiedNames = names.copy();
            """
        )

        self.assertEqual([], issues)

    def test_collection_methods_are_safe_across_union_receivers(self):
        issues = analyze(
            """
            list(int) | arr(int, 5) sequence = [1, 2];
            int size = sequence.length();
            int item = sequence.locate(0);
            sequence.append(3);
            list(int) removed = sequence.shave();

            list(int) | set(int) partlyMutable = [1];
            int commonSize = partlyMutable.length();
            partlyMutable.append(2);

            list(int) | list(str) mixed = [1];
            mixed.append(2);
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("not available on every type", issues[0].message)
        self.assertIn("every possible receiver", issues[1].message)

    def test_array_capacity_is_runtime_metadata(self):
        issues = analyze(
            """
            arr(int, 3) values = <1, 2>;
            arr(int, 8) alias = values;

            values.resize(8);

            arr(int, 1) sameStaticType = alias;
            arr(str, 3) wrongElementType = values;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("wrongElementType", issues[0].message)

    def test_search_results_are_nullable_and_aliases_are_exact(self):
        issues = analyze(
            """
            list(int) numbers = [1, 2];
            int definitelyFound = numbers.find_first(2);
            numbers.first_nth(2, 1);
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("definitelyFound", issues[0].message)
        self.assertIn("has no method named 'first_nth'", issues[1].message)

    def test_invalid_collection_method_calls_are_specific(self):
        issues = analyze(
            """
            list(int) numbers = [1, 2];
            list(str) words = ["thorn"];
            arr(int, 3) values = <1>;
            set(int) unique = (1, 2);

            numbers.append("bad");
            numbers.insert(1, "bad");
            numbers.length(1);
            numbers.shave(amount = "bad");
            numbers.copy(words);
            values.fill("bad");
            unique.append(3);
            numbers.length;
            numbers.unknown();
            """
        )

        self.assertEqual(9, len(issues))
        self.assertIn("Argument 1", issues[0].message)
        self.assertIn("Argument 2", issues[1].message)
        self.assertIn("expects 0 argument(s)", issues[2].message)
        self.assertIn("Argument 'amount'", issues[3].message)
        self.assertIn("expects 0 argument(s)", issues[4].message)
        self.assertIn("Argument 1", issues[5].message)
        self.assertIn("has no method named 'append'", issues[6].message)
        self.assertIn("must be called", issues[7].message)
        self.assertIn("has no method named 'unknown'", issues[8].message)

    def test_runic_collection_method_aliases_are_available(self):
        issues = analyze(
            """
            list(int) values = [1, 2];
            values.ᚢᛈᛖᚾᛞ(3);
            values.ᛁᚾᛋᚢᚱᛏ(4, 0);
            values.ᛈᚱᛁᛈᛖᚾᛞ(0);
            int replaced = values.ᚱᛁᛈᛚᛠᛋ_ᚫᛏ(9, 0);
            list(int) shortened = values.ᛋᚻᛟᛏᛖᚾ();
            int removed = values.ᚱᛁᛗᚣᚠ_ᚫᛏ(0);
            list(int) shaved = values.ᛋᚻᛠᚠ();
            int size = values.ᛚᛖᛝᚦ();
            int | nil first = values.ᚠᛠᚾᛞ_ᚠᚢᛋᛏ(2);
            int | nil nth = values.ᚠᛠᚾᛞ_ᚾᚦ(2, 1);
            int | nil last = values.ᚠᛠᚾᛞ_ᛚᚫᛋᛏ(2);
            int item = values.ᛚᚪᚳᛠᛏ(0);
            values.ᚳᚢᛗᛈᚱᛖᛋ();
            list(int) copied = values.ᚳᚪᛈᛁᛁ();

            arr(int, 3) array = <1>;
            array.ᚱᛁᛋᛠᛋ(4);
            int capacity = array.ᚳᚢᛈᛋᛁᛏᛁᛁ();
            array.ᚠᛁᛚ(0);
            array.ᛋᚳᛁᚾᛏᛠᛏ();
            array.ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ();
            """
        )

        self.assertEqual([], issues)


class ReturnSemanticTests(unittest.TestCase):
    def test_valid_returns_on_every_path(self):
        issues = analyze(
            """
            int choose(bool first) {
                if (first) {
                    return 1;
                } else {
                    return 2;
                }
            }

            nil perform() {
                return;
            }
            """
        )

        self.assertEqual([], issues)

    def test_invalid_return_types_placement_and_paths(self):
        issues = analyze(
            """
            int wrongType() {
                return "no";
            }

            int bare() {
                return;
            }

            nil givesValue() {
                return 1;
            }

            int missingPath(bool condition) {
                if (condition) {
                    return 1;
                }
            }

            return 1;
            """
        )

        self.assertEqual(5, len(issues))
        self.assertIn("must return a value of type 'int', got 'str'", issues[0].message)
        self.assertIn("Function 'bare' must return a value", issues[1].message)
        self.assertIn("Nil function 'givesValue'", issues[2].message)
        self.assertIn("on every path", issues[3].message)
        self.assertIn("outside a function", issues[4].message)


class ScopeAndInitializationTests(unittest.TestCase):
    def test_all_if_paths_can_definitely_initialize(self):
        issues = analyze(
            """
            nil use(bool condition) {
                int value;

                if (condition) {
                    value = 1;
                } else {
                    value = 2;
                }

                print(value);
            }
            """
        )

        self.assertEqual([], issues)

    def test_returning_branch_does_not_block_initialization(self):
        issues = analyze(
            """
            int choose(bool condition) {
                int value;

                if (condition) {
                    return 1;
                } else {
                    value = 2;
                }

                return value;
            }
            """
        )

        self.assertEqual([], issues)

    def test_conditional_declaration_has_function_scope(self):
        issues = analyze(
            """
            nil use(bool condition) {
                if (condition) {
                    int value = 1;
                }

                print(value);
            }
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("may be uninitialized", issues[0].message)
        self.assertNotIn("Unknown identifier", issues[0].message)

    def test_zero_iteration_loops_do_not_definitely_initialize(self):
        issues = analyze(
            """
            nil use() {
                while (false) {
                    int whileValue = 1;
                }

                for (i from 0 to 0) {
                    int forValue = i;
                }

                print(whileValue);
                print(forValue);
            }
            """
        )

        self.assertEqual(2, len(issues))
        self.assertTrue(all(
            "may be uninitialized" in issue.message
            for issue in issues
        ))

    def test_until_body_initializes_before_condition_and_exit(self):
        issues = analyze(
            """
            nil use() {
                until (ready) {
                    bool ready = true;
                    int value = 1;
                }

                print(value);
            }
            """
        )

        self.assertEqual([], issues)

    def test_uninitialized_read_and_compound_assignment(self):
        issues = analyze(
            """
            int first;
            int second = first;

            int count;
            count += 1;
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("may be uninitialized when used", issues[0].message)
        self.assertIn("before compound assignment", issues[1].message)

class SemanticRegressionTests(unittest.TestCase):
    def test_composite_string_does_not_crash(self):
        issues = analyze(
            '''
            str message = c"Hello, world";
            '''
        )

        self.assertEqual([], issues)

    def test_function_declaration_does_not_execute_body(self):
        issues = analyze(
            """
            int value;

            nil initialize() {
                value = 1;
            }

            print(value);
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "may be uninitialized",
            issues[0].message
        )

    def test_index_assignments_are_checked(self):
        issues = analyze(
            """
            list(int) values = [1];

            values["bad"] = 2;
            values[0] = "bad";

            set(int) immutable = (1, 2);
            immutable[0] = 3;
            """
        )

        self.assertEqual(3, len(issues))

        self.assertIn(
            "Collection index must have type 'int'",
            issues[0].message
        )

        self.assertIn(
            "indexed element",
            issues[1].message
        )

        self.assertIn(
            "immutable",
            issues[2].message
        )

    def test_any_cannot_flow_into_concrete_type(self):
        issues = analyze(
            """
            any unknown = 1;
            int concrete = unknown;
            any allowed = concrete;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "Cannot initialize variable 'concrete'",
            issues[0].message
        )

    def test_union_order_is_irrelevant(self):
        issues = analyze(
            """
            list(int | str) left = [1, "two"];
            list(str | int) right = ["two", 1];

            bool equal = left == right;
            """
        )

        self.assertEqual([], issues)

    def test_fresh_literals_do_not_create_unsafe_aliases(self):
        issues = analyze(
            """
            list(int | str) fresh = [1, 2];

            list(int) integers = [1, 2];
            list(int | str) unsafeAlias = integers;

            arr(int, 4) freshArray = <1, 2>;

            arr(int, 2) small = <1, 2>;
            arr(int, 4) capacityErasedAlias = small;
            """
        )

        self.assertEqual(1, len(issues))

        self.assertIn(
            "unsafeAlias",
            issues[0].message
        )

class BuiltinSemanticTests(unittest.TestCase):
    def test_native_python_import_declares_a_pyobject(self):
        issues = analyze(
            '''
            import python "math" as math;
            pyobject result = math.sqrt(25);
            '''
        )
        self.assertEqual([], issues)

    def test_native_python_import_obeys_duplicate_name_rules(self):
        issues = analyze(
            '''
            int math = 1;
            import python "math" as math;
            '''
        )
        self.assertTrue(any("already declared" in issue.message for issue in issues))

    def test_primitive_conversions_and_builtin_results(self):
        issues = analyze(
            '''
            any unknown = 5;
            int converted = int(unknown);
            float decimal = float("1.5");
            str text = str(10);
            char letter = char("x");
            bool truthy = bool(converted);

            int zero = int();
            float zeroFloat = float();
            str empty = str();
            char emptyChar = char();

            str response = input();
            int position = index(text);
            nil output = print(converted);
            '''
        )
        self.assertEqual([], issues)

    def test_builtin_argument_counts_and_types(self):
        issues = analyze(
            '''
            bool missing = bool();
            int excessive = int(1, 2);
            str badPreview = input(5);
            print("hello", 5);
            index();
            '''
        )
        self.assertEqual(5, len(issues))
        self.assertIn("Builtin 'bool' expects 1", issues[0].message)
        self.assertIn("Builtin 'int' expects between 0 and 1", issues[1].message)
        self.assertIn("Argument 1 to builtin 'input'", issues[2].message)
        self.assertIn("Argument 2 to builtin 'print'", issues[3].message)
        self.assertIn("Builtin 'index' expects 1", issues[4].message)

    def test_runic_conversion_keyword_is_normalized(self):
        issues = analyze(
            '''
            ᛁᚾᛏ value = ᛁᚾᛏ("5");
            ᛒᚣᛚ condition = ᛒᚣᛚ(value);
            '''
        )
        self.assertEqual([], issues)

    def test_non_mutating_collection_conversion_types_and_arguments(self):
        issues = analyze(
            '''
            list(int) values = list(int, [1, 2]);
            arr(int, 4) fixed = arr(int, values, capacity = 4);
            set(int) ordered = set(int, values);
            list(str) empty = list(str);
            '''
        )
        self.assertEqual([], issues)

        issues = analyze(
            '''
            arr(int, 2) badCapacity = arr(int, [1], capacity = "two");
            list(int) tooMany = list(int, [1], 2);
            '''
        )
        messages = [issue.message for issue in issues]
        self.assertTrue(any("must have type 'int'" in message for message in messages))
        self.assertTrue(any("expects" in message and "got 2" in message for message in messages))

    def test_string_length_and_collection_conversion_type_diagnostic(self):
        issues = analyze(
            '''
            str text = "abc";
            int asciiLength = text.length();
            int runicLength = text.ᛚᛖᛝᚦ();
            list(char) letters = list(char, text);
            list(char) mistaken = list(text);
            '''
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "requires an element type as its first argument",
            issues[0].message,
        )
        self.assertIn("list(T, text)", issues[0].message)

    def test_string_manipulation_method_types_and_named_arguments(self):
        issues = analyze(
            '''
            str text = "  Hello world  ";
            str lower = text.lower();
            str upper = text.upper();
            str stripped = text.strip(characters = " ");
            list(str) pieces = text.split(separator = " ");
            str changed = text.replace(
                old = "Hello",
                replacement = "Hi",
                count = 1
            );
            bool present = text.contains(substring = "world");
            '''
        )
        self.assertEqual([], issues)

    def test_string_methods_reject_coercion_and_bad_argument_counts(self):
        issues = analyze(
            '''
            str text = "Futhorc";
            text.lower(1);
            text.strip(1);
            text.split(1);
            text.replace("F", 1);
            text.replace("F", "Th", "once");
            text.contains(1);
            text.contains();
            '''
        )
        messages = [issue.message for issue in issues]
        self.assertEqual(7, len(issues))
        self.assertTrue(any("lower" in message and "expects 0 argument" in message for message in messages))
        self.assertEqual(4, sum("must have type 'str'" in message for message in messages))
        self.assertTrue(any("must have type 'int'" in message for message in messages))
        self.assertTrue(any("contains" in message and "missing required" in message for message in messages))

    def test_remaining_string_methods_and_text_join_types(self):
        issues = analyze(
            '''
            str text = "Futhorc";
            bool starts = text.starts_with(prefix = "Fu");
            bool ends = text.ends_with(suffix = "orc");
            int | nil position = text.find(substring = "th");
            int occurrences = text.count(substring = "o");

            str words = ["The", "Thorn"].join(separator = " ");
            str letters = ['r', 'u', 'n', 'e'].join();
            list(str | char) mixed = ["Futh", 'o', "rc"];
            str language = mixed.join();
            str names = arr(str, ["Iljeri", "Ciwa"]).join(" / ");
            str marks = set(char, ['!', '?']).join();
            '''
        )
        self.assertEqual([], issues)

    def test_string_search_and_join_reject_non_text_types(self):
        issues = analyze(
            '''
            str text = "Futhorc";
            text.starts_with(1);
            text.ends_with(false);
            text.find('F');
            text.count(1);

            list(int) numbers = [1, 2, 3];
            list(any) dynamic = ["one", "two"];
            numbers.join(",");
            dynamic.join();
            ["one", "two"].join(1);
            '''
        )
        messages = [issue.message for issue in issues]
        self.assertEqual(7, len(issues))
        self.assertEqual(5, sum("must have type 'str'" in message for message in messages))
        self.assertEqual(2, sum("has no method named 'join'" in message for message in messages))
        self.assertTrue(any("join" in message and "must have type 'str'" in message for message in messages))


class CompositeStringSemanticTests(unittest.TestCase):
    def test_interpolations_parse_and_validate_expressions(self):
        issues = analyze(
            r'''
            str name = "Matalya";
            int age = 26;
            bool awake = true;
            nil nothing = nil;
            list(int) values = [1, 2, 3];
            any dynamic = values;

            str message = c"Name: {name}; age: {age}; awake: {awake}; nil: {nothing}; values: {values}; any: {dynamic}; math: {age + 1}; conversion: {str(age)}";
            '''
        )

        self.assertEqual([], issues)

    def test_interpolation_reports_embedded_expression_errors(self):
        issues = analyze(
            r'''
            str missing = c"Missing: {unknown}";
            str badMath = c"Bad math: {1 + "two"}";
            '''
        )

        self.assertEqual(2, len(issues))
        self.assertIn(
            "Unknown identifier 'unknown'",
            issues[0].message
        )
        self.assertIn(
            "Operator '+' cannot be applied",
            issues[1].message
        )

    def test_escaped_braces_and_runic_prefix_are_supported(self):
        issues = analyze(
            r'''
            int value = 5;
            str escaped = c"Literal: \{value\}";
            str runic = ᚳ"Value: {value}";
            '''
        )

        self.assertEqual([], issues)

    def test_empty_interpolation_is_rejected(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "interpolation cannot be empty"
        ):
            analyze(
                'str invalid = c"Empty: {}";'
            )


class NamedTypeSemanticTests(unittest.TestCase):
    def test_unknown_named_types_are_reported_recursively(self):
        issues = analyze(
            """
            Person person;
            list(Person) people;
            Person | nil owner;
            arr(list(Person | nil), 4) graph;
            """
        )

        self.assertEqual(4, len(issues))
        self.assertTrue(all(
            issue.message == "Unknown type 'Person'."
            for issue in issues
        ))

    def test_type_and_value_names_use_separate_namespaces(self):
        issues = analyze(
            """
            int Person = 5;
            Person value;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertEqual(
            "Unknown type 'Person'.",
            issues[0].message
        )

    def test_predeclared_types_support_forward_references(self):
        program = parseProgram(
            """
            Person first;
            list(Person | nil) chain;
            """
        )

        # Put the declaration after its uses. The analyzer's type
        # prepass must still make it available to both declarations.
        program.statements.append(
            NamedTypeDeclaration(
                Identifier("Person"),
                kind="struct"
            )
        )

        issues = SemanticAnalyzer().analyze(program)
        self.assertEqual([], issues)


class BasicStructSemanticTests(unittest.TestCase):
    def test_parser_builds_struct_declarations_and_literals(self):
        program = parseProgram(
            """
            struct Person {
                str name;
                int age = 18;
                const str species = "human";
            }

            Person contextual = {
                name = "Context";
            };

            Person explicit = Person {
                name = "Explicit";
                age = 20
            };
            """
        )

        declaration = program.statements[0]
        self.assertIsInstance(declaration, StructDeclaration)
        self.assertEqual("Person", declaration.name.name)
        self.assertEqual(3, len(declaration.fields))
        self.assertIsInstance(
            declaration.fields[0].defaultValue,
            Uninitialized
        )
        self.assertTrue(
            declaration.fields[2].modifiers.isConst
        )

        contextual = program.statements[1].varValue
        explicit = program.statements[2].varValue
        self.assertIsInstance(contextual, StructLiteral)
        self.assertIsNone(contextual.typeName)
        self.assertEqual("Person", explicit.typeName.name)
        self.assertIsNotNone(declaration.span)
        self.assertIsNotNone(explicit.span)

    def test_defaults_forward_fields_and_contextual_literals(self):
        issues = analyze(
            """
            Person makePerson(str name) {
                return {
                    name = name;
                    address = Address { city = "Buenos Aires"; };
                };
            }

            nil accept(Person person) {
                return;
            }

            struct Person {
                str name;
                Address address;
                int age = 18;
            }

            struct Address {
                str city;
            }

            Person person = makePerson("Matias");
            person = {
                name = "Lucas";
                address = { city = "Cordoba"; };
            };

            accept({
                name = "Ada";
                address = Address { city = "London"; };
            });

            list(Person) people = [{
                name = "Grace";
                address = Address { city = "New York"; };
            }];
            """
        )

        self.assertEqual([], issues)

    def test_struct_literal_field_errors_are_specific(self):
        issues = analyze(
            """
            struct Person {
                str name;
                int age = 18;
            }

            Person person = {
                age = "old";
                age = 20;
                nickname = "Thorny";
            };
            """
        )

        self.assertEqual(4, len(issues))
        self.assertIn("Field 'age'", issues[0].message)
        self.assertIn("initialized more than once", issues[1].message)
        self.assertIn("no field named 'nickname'", issues[2].message)
        self.assertIn("Missing required field 'name'", issues[3].message)

    def test_struct_declaration_errors(self):
        issues = analyze(
            """
            struct Invalid {
                global int globalField;
                new int replacedField;
                int duplicate;
                str duplicate;
                int badDefault = "wrong";
            }
            """
        )

        self.assertEqual(4, len(issues))
        self.assertIn("cannot use the 'global' modifier", issues[0].message)
        self.assertIn("cannot use the 'new' modifier", issues[1].message)
        self.assertIn("declares field 'duplicate' more than once", issues[2].message)
        self.assertIn("Default value", issues[3].message)

    def test_ambiguous_anonymous_union_requires_explicit_type(self):
        issues = analyze(
            """
            struct First { int value; }
            struct Second { int value; }

            First | Second ambiguous = { value = 1; };
            First | Second explicit = First { value = 1; };
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("is ambiguous", issues[0].message)

    def test_contextual_return_literals_are_validated(self):
        issues = analyze(
            """
            struct Person {
                str name;
                int age;
            }

            Person badType() {
                return {
                    name = 123;
                    age = 20;
                };
            }

            Person missingField() {
                return {
                    name = "Ada";
                };
            }

            Person valid() {
                return {
                    name = "Grace";
                    age = 30;
                };
            }
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("Field 'name'", issues[0].message)
        self.assertIn("Missing required field 'age'", issues[1].message)

    def test_anonymous_literals_require_a_concrete_struct_context(self):
        issues = analyze(
            """
            struct Person { str name; }

            { name = "Standalone"; };
            str name = { name = "Member"; }.name;
            any value = { name = "Any variable"; };

            any makeThing() {
                return { name = "Any return"; };
            }

            print({ name = "Any argument"; });

            any explicitValue = Person { name = "Explicit"; };
            print(Person { name = "Explicit argument"; });
            """
        )

        self.assertEqual(5, len(issues))
        self.assertTrue(all(
            issue.message == (
                "Cannot infer the type of this anonymous struct "
                "literal; use an explicit struct name."
            )
            for issue in issues
        ))

    def test_parser_preserves_instance_and_static_methods(self):
        program = parseProgram(
            """
            struct Person {
                str name;

                nil rename(Person self, str name) {
                    self.name = name;
                }

                Person choose(Person left, Person right) {
                    return left;
                }
            }
            """
        )

        declaration = program.statements[0]
        self.assertEqual(1, len(declaration.fields))
        self.assertEqual(2, len(declaration.methods))
        self.assertEqual(
            "self",
            declaration.methods[0].parameters[0].name.name
        )
        self.assertEqual(
            "choose",
            declaration.methods[1].name.name
        )


class StructMemberSemanticTests(unittest.TestCase):
    def test_nested_member_reads_and_writes_infer_field_types(self):
        issues = analyze(
            """
            struct Address {
                str city;
            }

            struct Person {
                str name;
                int age;
                Address address;
                list(int) scores;
            }

            const Person person = {
                name = "Ada";
                age = 30;
                address = Address { city = "London"; };
                scores = [10, 20];
            };

            str name = person.name;
            str city = person.address.city;
            int score = person.scores[0];
            bool adult = person.age >= 18;

            person.name = "Grace";
            person.age += 1;
            person.address.city = "New York";
            person.scores[0] = 25;
            """
        )

        self.assertEqual([], issues)

    def test_unknown_non_struct_const_and_type_errors(self):
        issues = analyze(
            """
            struct Person {
                str name;
                const int id;
            }

            Person person = { name = "Ada"; id = 1; };
            int scalar = 1;

            str missing = person.nickname;
            int invalidTarget = scalar.value;
            person.name = 10;
            person.name += "suffix";
            person.id = 2;
            """
        )

        self.assertEqual(5, len(issues))
        self.assertIn("has no field named 'nickname'", issues[0].message)
        self.assertIn("Cannot access member 'value'", issues[1].message)
        self.assertIn("Cannot assign a value of type 'int'", issues[2].message)
        self.assertIn("Operator '+' cannot be applied", issues[3].message)
        self.assertIn("const struct field 'id'", issues[4].message)

    def test_union_member_reads_require_a_common_field(self):
        issues = analyze(
            """
            struct NumberValue { int value; }
            struct TextValue { str value; }
            struct Other { bool flag; }

            NumberValue | TextValue common = NumberValue { value = 1; };
            int | str value = common.value;

            NumberValue | Other incomplete = Other { flag = true; };
            int missing = incomplete.value;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("not available on every type in union", issues[0].message)

    def test_union_member_writes_must_be_safe_for_every_variant(self):
        issues = analyze(
            """
            struct First { int value; }
            struct AlsoInt { int value; }
            struct Text { str value; }
            struct Locked { const int value; }

            First | AlsoInt safe = First { value = 1; };
            safe.value = 2;
            safe.value += 1;

            First | Text incompatible = First { value = 1; };
            incompatible.value = 2;

            First | Locked partlyLocked = First { value = 1; };
            partlyLocked.value = 2;
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("Cannot assign a value of type 'int'", issues[0].message)
        self.assertIn("const struct field 'value'", issues[1].message)

    def test_union_member_write_rejects_ambiguous_anonymous_struct(self):
        issues = analyze(
            """
            struct FirstValue { int value; }
            struct SecondValue { int value; }

            struct FirstBox { FirstValue item; }
            struct SecondBox { SecondValue item; }

            FirstBox | SecondBox box = FirstBox {
                item = FirstValue { value = 1; };
            };

            box.item = { value = 2; };

            struct SharedBox { FirstValue item; }
            FirstBox | SharedBox shared = FirstBox {
                item = FirstValue { value = 1; };
            };

            shared.item = { value = 3; };
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("is ambiguous", issues[0].message)


    def test_union_member_write_checks_non_struct_variants(self):
        issues = analyze(
            """
            struct Person { str name; }
            struct PersonBox { Person item; }
            struct IntBox { int item; }

            PersonBox | IntBox box = PersonBox {
                item = Person { name = "Ada"; };
            };

            box.item = { name = "Grace"; };
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "Cannot assign a value of type 'Person'",
            issues[0].message
        )


class StructMethodSemanticTests(unittest.TestCase):
    def test_bare_self_parameter_has_specific_parser_error(self):
        cases = (
            (
                "self",
                "struct Product { nil restock(self, int amount) {} }",
                "Product self",
            ),
            (
                "ᛋᛖᛚᚠ",
                "ᛋᛏᚱᚢᚳᛏ Product { ᚾᛁᛚ restock(ᛋᛖᛚᚠ, ᛁᚾᛏ amount) {} }",
                "Product ᛋᛖᛚᚠ",
            ),
        )

        for spelling, source, expectedForm in cases:
            with self.subTest(spelling=spelling):
                with self.assertRaises(TokenError) as context:
                    parseProgram(source)
                message = str(context.exception)
                self.assertIn("is missing its type", message)
                self.assertIn(expectedForm, message)

    def test_instance_static_and_union_methods_support_defaults_and_names(self):
        issues = analyze(
            """
            struct Messenger {
                str prefix;

                str send(
                    Messenger self,
                    str name,
                    str punctuation = "!"
                ) {
                    return c"{self.prefix} {name}{punctuation}";
                }

                Messenger create(str prefix = "Hello") {
                    return { prefix = prefix; };
                }
            }

            struct OtherMessenger {
                str prefix;

                str send(
                    OtherMessenger self,
                    str name,
                    str punctuation = "?"
                ) {
                    return c"{self.prefix} {name}{punctuation}";
                }
            }

            Messenger messenger = Messenger.create();
            str named = messenger.send(
                punctuation = "?",
                name = "Ada"
            );

            Messenger | OtherMessenger common = messenger;
            str commonResult = common.send(name = "Grace");
            """
        )

        self.assertEqual([], issues)

    def test_method_named_arguments_must_bind_every_union_receiver(self):
        issues = analyze(
            """
            struct First {
                int value;
                nil update(First self, int value = 1) {
                    self.value = value;
                }
            }

            struct Second {
                int value;
                nil update(Second self, int amount = 1) {
                    self.value = amount;
                }
            }

            First | Second item = First { value = 0; };
            item.update();
            item.update(2);
            item.update(value = 3);
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn(
            "not valid for every possible receiver",
            issues[0].message
        )

    def test_self_parameter_cannot_have_a_default(self):
        issues = analyze(
            """
            struct Counter {
                int value;

                nil reset(
                    Counter self = Counter { value = 0; }
                ) {
                    self.value = 0;
                }
            }
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("'self' parameter cannot have", issues[0].message)

    def test_instance_and_static_methods_are_checked_and_inferred(self):
        issues = analyze(
            """
            struct Counter {
                int value;

                nil add(Counter self, int amount) {
                    self.value += amount;
                }

                int current(Counter self) {
                    return self.value;
                }

                Counter larger(Counter left, Counter right) {
                    if (left.value > right.value) {
                        return left;
                    } else {
                        return right;
                    }
                }
            }

            const Counter counter = { value = 1; };
            counter.add(2);
            int current = counter.current();
            Counter larger = Counter.larger(
                counter,
                Counter { value = 3; }
            );
            """
        )

        self.assertEqual([], issues)

    def test_method_arguments_propagate_struct_context(self):
        issues = analyze(
            """
            struct Address { str city; }

            struct Person {
                str name;
                Address address;

                nil move(Person self, Address address) {
                    self.address = address;
                }

                Person renamed(Person self, str name) {
                    return {
                        name = name;
                        address = self.address;
                    };
                }

                Person at(Address address, str name) {
                    return {
                        name = name;
                        address = address;
                    };
                }
            }

            Person person = {
                name = "Ada";
                address = Address { city = "London"; };
            };

            person.move({ city = "Paris"; });
            Person renamed = person.renamed("Grace");
            Person visitor = Person.at(
                { city = "Rome"; },
                "Lin"
            );
            """
        )

        self.assertEqual([], issues)

    def test_invalid_method_calls_are_specific(self):
        issues = analyze(
            """
            struct Person {
                str name;

                nil rename(Person self, str name) {
                    self.name = name;
                }

                Person choose(Person left, Person right) {
                    return left;
                }
            }

            Person person = { name = "Ada"; };

            person.name();
            person.rename();
            person.rename(2);
            Person.rename("Grace");
            person.choose(person, person);
            person.missing();
            """
        )

        self.assertEqual(6, len(issues))
        self.assertIn("field 'name' is not callable", issues[0].message)
        self.assertIn("expects 1 argument(s), got 0", issues[1].message)
        self.assertIn("must have type 'str', got 'int'", issues[2].message)
        self.assertIn("must be called on a 'Person' value", issues[3].message)
        self.assertIn("must be called through struct type", issues[4].message)
        self.assertIn("no instance method named 'missing'", issues[5].message)

    def test_self_rules_and_method_declaration_conflicts(self):
        issues = analyze(
            """
            struct Other { int value; }

            struct Invalid {
                int value;

                nil value(Invalid self) {
                }

                nil wrong(Other self) {
                }

                nil misplaced(int amount, Invalid self) {
                }

                nil repeated(Invalid self) {
                }

                nil repeated(Invalid self) {
                }

                nil replace(Invalid self, Invalid other) {
                    self = other;
                }
            }

            nil freeFunction(Invalid self) {
            }

            print(self);
            """
        )

        self.assertEqual(7, len(issues))
        self.assertIn("both a field and a method", issues[0].message)
        self.assertIn("must have type 'Invalid'", issues[1].message)
        self.assertIn("must be the first parameter", issues[2].message)
        self.assertIn("method 'repeated' more than once", issues[3].message)
        self.assertIn("Cannot reassign const variable 'self'", issues[4].message)
        self.assertIn("reserved 'self' parameter", issues[5].message)
        self.assertIn("only be used inside an instance method", issues[6].message)

    def test_union_method_calls_require_every_receiver_to_support_them(self):
        issues = analyze(
            """
            struct NumberBox {
                int value;
                int get(NumberBox self) { return self.value; }
                nil change(NumberBox self, int value) {
                    self.value = value;
                }
            }

            struct TextBox {
                str value;
                str get(TextBox self) { return self.value; }
                nil change(TextBox self, str value) {
                    self.value = value;
                }
            }

            struct EmptyBox { bool empty; }

            NumberBox | TextBox common = NumberBox { value = 1; };
            int | str value = common.get();
            common.change(2);

            NumberBox | EmptyBox incomplete = EmptyBox { empty = true; };
            int missing = incomplete.get();
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("every possible receiver", issues[0].message)
        self.assertIn("not available on every type in union", issues[1].message)

    def test_method_returns_and_runic_self_are_validated(self):
        issues = analyze(
            """
            struct Person {
                str name;

                nil rename(Person ᛋᛖᛚᚠ, str name) {
                    ᛋᛖᛚᚠ.name = name;
                }

                Person broken(Person self) {
                    return { name = 1; };
                }

                int missing(Person self) {
                    if (true) {
                        return 1;
                    }
                }
            }

            Person person = { name = "Ada"; };
            person.rename("Grace");
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("Field 'name'", issues[0].message)
        self.assertIn("on every path", issues[1].message)


class EnumSemanticTests(unittest.TestCase):
    def test_parser_and_analyzer_resolve_auto_incremented_values(self):
        program = parseProgram(
            """
            enum(int) Position = (
                FIRST = 1 + 1;
                SECOND;
                THIRD
            )
            """
        )
        declaration = program.statements[0]

        self.assertIsInstance(declaration, EnumDeclaration)
        self.assertEqual("Position", declaration.name.name)
        self.assertEqual(3, len(declaration.members))

        issues = SemanticAnalyzer().analyze(program)

        self.assertEqual([], issues)
        self.assertEqual(
            [2, 3, 4],
            [
                member.resolvedValue
                for member in declaration.members
            ]
        )

    def test_enum_members_and_declared_raw_values_are_assignable(self):
        issues = analyze(
            """
            Weather forwardRaw = 1;
            Weather forwardNamed = RAINY;

            enum(int) Weather = (
                SUNNY;
                RAINY;
                STORMY
            )

            enum(str) Color = (
                RED = "red";
                BLUE = "blue"
            )

            Weather tomorrow(Weather weather) {
                return weather;
            }

            struct Report {
                Weather weather = SUNNY;
            }

            Weather current = SUNNY;
            current = Weather.RAINY;
            Weather raw = 2;
            Color red = "red";
            list(Weather) forecast = [0, Weather.STORMY];
            Weather next = tomorrow(1);
            Report report = {};
            """
        )

        self.assertEqual([], issues)

    def test_invalid_enum_values_members_and_mutation_are_reported(self):
        issues = analyze(
            """
            enum(int) Weather = (
                SUNNY;
                RAINY;
                STORMY
            )

            int dynamic = 1;
            Weather cloudy = 3;
            Weather unknownAtCompileTime = dynamic;
            Weather.SUNNY = 2;
            SUNNY = RAINY;
            Weather missing = Weather.CLOUDY;
            Weather.SUNNY();
            """
        )

        self.assertEqual(6, len(issues))
        self.assertIn("not a declared value of enum 'Weather'", issues[0].message)
        self.assertIn("Cannot initialize variable", issues[1].message)
        self.assertIn("enum members are constant", issues[2].message)
        self.assertIn("enum members are constant", issues[3].message)
        self.assertIn("has no member named 'CLOUDY'", issues[4].message)
        self.assertIn("is not callable", issues[5].message)

    def test_enum_declaration_errors_are_specific(self):
        issues = analyze(
            """
            int dynamic = 2;

            enum(str) Labels = (
                MISSING;
                WRONG = 2;
                FIRST_LABEL = "same";
                SECOND_LABEL = "same"
            )

            enum(int) Broken = (
                DYNAMIC = dynamic;
                AFTER_DYNAMIC;
                DUPLICATE = 1;
                DUPLICATE = 2
            )

            enum(int) Empty = ()
            """
        )

        self.assertEqual(7, len(issues))
        self.assertIn("only int-backed enums can auto-increment", issues[0].message)
        self.assertIn("must have backing type 'str'", issues[1].message)
        self.assertIn("assigns value 'same'", issues[2].message)
        self.assertIn("compile-time constant", issues[3].message)
        self.assertIn("Cannot auto-increment", issues[4].message)
        self.assertIn("member 'DUPLICATE' more than once", issues[5].message)
        self.assertIn("must declare at least one member", issues[6].message)

    def test_reused_member_names_and_union_values_require_qualification(self):
        issues = analyze(
            """
            enum(int) First = (
                UNKNOWN = 0;
                FIRST_ONLY = 1
            )

            enum(int) Second = (
                UNKNOWN = 0;
                SECOND_ONLY = 2
            )

            First first = First.UNKNOWN;
            Second second = Second.UNKNOWN;
            First | Second uniqueRaw = 1;
            First | Second qualified = First.UNKNOWN;

            First ambiguousName = UNKNOWN;
            First | Second ambiguousRaw = 0;
            First wrongEnum = Second.SECOND_ONLY;
            """
        )

        self.assertEqual(3, len(issues))
        self.assertIn("member name 'UNKNOWN' is ambiguous", issues[0].message)
        self.assertIn("Enum value is ambiguous", issues[1].message)
        self.assertIn("Cannot initialize variable 'wrongEnum'", issues[2].message)

    def test_union_field_enum_writes_resolve_one_nominal_type(self):
        issues = analyze(
            """
            enum(int) FirstState = ( READY = 0; )
            enum(int) SecondState = ( READY = 0; )
            enum(int) ThirdState = ( WAITING = 1; )

            struct FirstBox { FirstState state; }
            struct SecondBox { SecondState state; }
            struct ThirdBox { ThirdState state; }

            FirstBox | SecondBox ambiguous = FirstBox {
                state = FirstState.READY;
            };
            ambiguous.state = 0;

            FirstBox | ThirdBox unsafe = FirstBox {
                state = FirstState.READY;
            };
            unsafe.state = 0;
            """
        )

        self.assertEqual(2, len(issues))
        self.assertIn("Enum value is ambiguous", issues[0].message)
        self.assertIn("Cannot assign a value of type 'FirstState'", issues[1].message)

    def test_constant_folded_enum_values_must_match_their_thorn_type(self):
        program = parseProgram(
            """
            enum(int) Fraction = (
                HALF = 2 ^ -1;
            )

            enum(int) Floored = (
                VALUE = 5.0 // 2;
            )

            enum(float) Imaginary = (
                VALUE = (-1) ^ 0.5;
            )
            """
        )

        issues = SemanticAnalyzer().analyze(program)

        self.assertEqual(2, len(issues))
        self.assertTrue(all(
            "cannot be represented as inferred type" in issue.message
            for issue in issues
        ))
        self.assertFalse(
            program.statements[0].members[0].hasResolvedValue
        )
        self.assertTrue(
            program.statements[1].members[0].hasResolvedValue
        )
        self.assertEqual(
            2,
            program.statements[1].members[0].resolvedValue
        )
        self.assertFalse(
            program.statements[2].members[0].hasResolvedValue
        )

    def test_character_literals_must_decode_to_one_character(self):
        program = parseProgram(
            """
            char broken = 'ab';
            char newline = '\\n';

            enum(char) Broken = (
                TOO_LONG = 'ab';
                EMPTY = '';
            )
            """
        )

        issues = SemanticAnalyzer().analyze(program)

        self.assertEqual(3, len(issues))
        self.assertTrue(all(
            "decode to exactly one character" in issue.message
            for issue in issues
        ))
        self.assertTrue(all(
            not member.hasResolvedValue
            for member in program.statements[2].members
        ))

    def test_qualified_enum_members_survive_value_namespace_shadowing(self):
        issues = analyze(
            """
            enum(int) Weather = ( SUNNY = 0; )
            int Weather = 5;
            Weather current = Weather.SUNNY;

            enum(int) First = ( VALUE = 0; )
            enum(int) Second = ( First = 1; )
            First first = First.VALUE;

            enum(int) Third = ( THIRD_VALUE = 0; )
            int Third() { return 1; }
            Third third = Third.THIRD_VALUE;
            """
        )

        self.assertEqual([], issues)

    def test_genuinely_ambiguous_qualified_members_are_reported(self):
        issues = analyze(
            """
            enum(int) Weather = ( SUNNY = 0; )
            struct Holder { int SUNNY; }

            Holder Weather = { SUNNY = 1; };
            Weather current = Weather.SUNNY;
            """
        )

        self.assertEqual(1, len(issues))
        self.assertIn("type and value namespaces", issues[0].message)

    def test_raw_enum_value_can_satisfy_enum_and_any_union_members(self):
        issues = analyze(
            """
            enum(int) State = ( READY = 0; )

            struct StateBox {
                State value;
                nil update(StateBox self, State value) {
                    self.value = value;
                }
            }

            struct AnyBox {
                any value;
                nil update(AnyBox self, any value) {
                    self.value = value;
                }
            }

            StateBox | AnyBox box = StateBox {
                value = State.READY;
            };

            box.value = 0;
            box.update(0);
            """
        )

        self.assertEqual([], issues)

    def test_enum_backing_types_are_concrete_comparable_primitives(self):
        validIssues = analyze(
            """
            enum(int) Number = ( ONE = 1; )
            enum(float) Ratio = ( HALF = 0.5; )
            enum(str) Text = ( WORD = "thorn"; )
            enum(char) Letter = ( A = 'a'; )
            enum(bool) Toggle = ( OFF = false; ON = true; )
            """
        )
        invalidIssues = analyze(
            """
            enum(any) Mixed = ( VALUE = 1; )
            enum(nil) Nothing = ( VALUE = nil; )
            enum(int | str) UnionBacked = ( VALUE = 1; )
            enum(list(int)) CollectionBacked = ( VALUE = [1]; )
            """
        )

        self.assertEqual([], validIssues)
        self.assertEqual(4, len(invalidIssues))
        self.assertTrue(all(
            "backing type" in issue.message
            for issue in invalidIssues
        ))


class DictionarySemanticTests(unittest.TestCase):
    def test_dictionary_types_literals_indices_and_methods(self):
        issues = analyze(
            '''
            enum(int) Kind = (HEALTH; STRENGTH)
            dict(str | int, int) scores = {
                "Ada" -> 10;
                2 -> 20
            };
            dict(Kind, str) labels = { HEALTH -> "healing"; };
            dict(str, int) empty = {};
            scores["Ada"] += 1;
            scores["Grace"] = 30;
            int value = scores[2];
            int | nil fallback = scores.get("missing");
            bool present = scores.has("Ada");
            list(str | int) keys = scores.keys();
            list(int) values = scores.values();
            list(arr(str | int, 2)) items = scores.items();
            int removed = scores.remove("Ada");
            int size = scores.length();
            dict(str | int, int) copied = scores.copy();
            scores.clear();
            '''
        )
        self.assertEqual([], issues)

    def test_dictionary_key_and_value_errors_are_specific(self):
        issues = analyze(
            '''
            dict(list(int), int) impossible;
            dict(any, int) badLiteral = { [1, 2] -> 3; };
            dict(str, int) scores = { "Ada" -> 10; };
            int wrongKey = scores[1];
            scores["Ada"] = "high";
            scores[0:1];
            scores.has(1);
            '''
        )
        messages = [issue.message for issue in issues]
        self.assertTrue(any("key type 'list(int)' is not hashable" in message for message in messages))
        self.assertTrue(any("key value has unhashable type 'list(int)'" in message for message in messages))
        self.assertTrue(any("Dictionary key must have type 'str'" in message for message in messages))
        self.assertTrue(any("indexed element" in message and "int" in message for message in messages))
        self.assertTrue(any("Dictionary values cannot be sliced" in message for message in messages))
        self.assertTrue(any("Argument 1" in message and "str" in message for message in messages))

    def test_dictionary_constructor_is_typed(self):
        issues = analyze(
            '''
            pyobject builtins = pyimport("builtins");
            dict(str, int) copied = dict(str, int, builtins.dict(a = 1));
            dict(str, int) empty = dict(str, int);
            bool verified = is_dict(copied);
            '''
        )
        self.assertEqual([], issues)


class NamedTypeDeclarationRegressionTests(unittest.TestCase):
    def test_duplicate_type_names_are_rejected(self):
        program = parseProgram("")
        program.statements.extend([
            NamedTypeDeclaration(
                Identifier("Thing"),
                kind="struct"
            ),
            NamedTypeDeclaration(
                Identifier("Thing"),
                kind="enum"
            )
        ])

        issues = SemanticAnalyzer().analyze(program)

        self.assertEqual(1, len(issues))
        self.assertEqual(
            "Type 'Thing' is already declared in this scope.",
            issues[0].message
        )

    def test_function_bodies_predeclare_local_types(self):
        program = parseProgram(
            """
            nil use() {
                Local value;
            }
            """
        )

        function = program.statements[0]
        function.body.statements.append(
            NamedTypeDeclaration(
                Identifier("Local"),
                kind="struct"
            )
        )

        issues = SemanticAnalyzer().analyze(program)
        self.assertEqual([], issues)

    def test_local_type_cannot_shadow_a_visible_type(self):
        issues = analyze(
            """
            struct Thing { int value; }

            Thing outer = { value = 1; };

            nil test() {
                struct Thing { str value; }
                Thing inner = outer;
            }
            """
        )

        self.assertEqual(1, len(issues))
        self.assertEqual(
            (
                "Type 'Thing' cannot shadow a type declared "
                "in an outer scope."
            ),
            issues[0].message
        )


    def test_control_flow_bodies_hoist_types_to_function_scope(self):
        issues = analyze(
            """
            nil use(bool condition) {
                Local value = { name = "Ada"; };

                if (condition) {
                    struct Local { str name; }
                }
            }
            """
        )

        self.assertEqual([], issues)

    def test_control_flow_bodies_hoist_functions_to_function_scope(self):
        issues = analyze(
            """
            nil outer() {
                helper();

                if (true) {
                    nil helper() {
                        return;
                    }
                }
            }
            """
        )

        self.assertEqual([], issues)



if __name__ == "__main__":
    unittest.main()
