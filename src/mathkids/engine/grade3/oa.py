"""Grade 3 Operations & Algebraic Thinking skills."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, SequenceAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register

_DOMAIN = "Operations & Algebraic Thinking"

_GROUP_NOUNS = ("bags", "boxes", "baskets", "shelves", "rows", "plates", "jars")
_ITEM_NOUNS = ("apples", "marbles", "stickers", "cookies", "crayons", "pencils", "books")
_KID_NAMES = ("Mia", "Leo", "Ava", "Sam", "Zoe", "Jack", "Nina", "Eli")


class MeaningOfMultiplication(Skill):
    id = "3.OA.A.1"
    slug = "g3-meaning-multiplication"
    grade = 3
    domain = _DOMAIN
    title = "Meaning of multiplication"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(2, 5), rng.randint(2, 5)
        elif level == 2:
            a, b = rng.randint(2, 8), rng.randint(2, 8)
        else:
            a, b = rng.randint(1, 10), rng.randint(1, 10)
        groups = rng.choice(_GROUP_NOUNS)
        items = rng.choice(_ITEM_NOUNS)
        prompt = (
            f"There are {a} {groups} with {b} {items} in each. "
            f"How many {items} are there in all? ({a} groups of {b} = ?)"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(a * b),
            payload={"a": a, "b": b, "groups": groups, "items": items},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Multiplication is a fast way to add equal groups. '4 groups of 5' means "
                "5 + 5 + 5 + 5, which we write as 4 × 5 = 20. The first number is how many "
                "groups, the second is how many in each group."
            ),
            strategy="Equal groups? Multiply: (number of groups) × (size of each group).",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b = problem.payload["a"], problem.payload["b"]
        return [
            f"You have {a} equal groups of {b}.",
            f"Add {b} a total of {a} times, or just compute {a} × {b}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b = problem.payload["a"], problem.payload["b"]
        return f"{a} groups of {b} means {a} × {b} = {a * b}."


class MeaningOfDivision(Skill):
    id = "3.OA.A.2"
    slug = "g3-meaning-division"
    grade = 3
    domain = _DOMAIN
    title = "Meaning of division"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            q, d = rng.randint(2, 5), rng.randint(2, 5)
        elif level == 2:
            q, d = rng.randint(2, 9), rng.randint(2, 8)
        else:
            q, d = rng.randint(2, 10), rng.randint(2, 10)
        total = q * d  # build the dividend so the split is exactly whole
        names = rng.choice(_KID_NAMES)
        items = rng.choice(_ITEM_NOUNS)
        prompt = (
            f"{names} shares {total} {items} equally among {d} friends. "
            f"How many {items} does each friend get? ({total} ÷ {d} = ?)"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(q),
            payload={"total": total, "d": d, "q": q, "items": items, "name": names},
        )

    def invariant(self, problem: Problem) -> bool:
        total, d = problem.payload["total"], problem.payload["d"]
        return total == problem.answer.value * d and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Division splits a total into equal groups. 12 ÷ 3 asks 'if I share 12 things "
                "equally among 3 groups, how many in each group?' The answer is 4 because "
                "3 × 4 = 12. Division and multiplication are opposites."
            ),
            strategy="Sharing equally? Divide: total ÷ number of groups = size of each group.",
        )

    def hints(self, problem: Problem) -> list[str]:
        total, d = problem.payload["total"], problem.payload["d"]
        return [
            f"Split {total} into {d} equal groups.",
            f"Ask: what number times {d} makes {total}?",
        ]

    def worked_example(self, problem: Problem) -> str:
        total, d, q = problem.payload["total"], problem.payload["d"], problem.payload["q"]
        return f"{total} ÷ {d}: since {d} × {q} = {total}, each group gets {q}."


class MulDivWordProblems(Skill):
    id = "3.OA.A.3"
    slug = "g3-muldiv-word-problems"
    grade = 3
    domain = _DOMAIN
    title = "Multiply & divide word problems within 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        items = rng.choice(_ITEM_NOUNS)
        name = rng.choice(_KID_NAMES)
        do_multiply = rng.random() < 0.5
        if do_multiply:
            if level <= 1:
                a, b = rng.randint(2, 5), rng.randint(2, 5)
            elif level == 2:
                a, b = rng.randint(2, 9), rng.randint(2, 9)
            else:
                a = rng.randint(2, 10)
                b = rng.randint(2, 100 // a)  # keep the product within 100
            prompt = (
                f"{name} packs {a} boxes with {b} {items} in each box. "
                f"How many {items} in all?"
            )
            answer = a * b
        else:
            if level <= 1:
                q, d = rng.randint(2, 5), rng.randint(2, 5)
            elif level == 2:
                q, d = rng.randint(2, 9), rng.randint(2, 9)
            else:
                d = rng.randint(2, 10)
                q = rng.randint(2, 100 // d)  # dividend stays within 100
            total = q * d
            prompt = (
                f"{name} puts {total} {items} into {d} equal boxes. "
                f"How many {items} go in each box?"
            )
            answer = q
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"multiply": do_multiply, "items": items, "name": name},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Word problems hide a multiply or a divide. Equal groups joined together "
                "means multiply. A total being shared into equal groups means divide. "
                "Read carefully, decide the operation, then compute."
            ),
            strategy="Joining equal groups? Multiply. Sharing a total equally? Divide.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["multiply"]:
            return [
                "Equal groups are being put together, so this is multiplication.",
                "Multiply the number of boxes by how many are in each box.",
            ]
        return [
            "A total is being shared into equal groups, so this is division.",
            "Divide the total by the number of boxes.",
        ]

    def worked_example(self, problem: Problem) -> str:
        if problem.payload["multiply"]:
            return f"Equal groups joined → multiply. The answer is {problem.answer.value}."
        return f"A total shared equally → divide. The answer is {problem.answer.value}."


class UnknownInEquation(Skill):
    id = "3.OA.A.4"
    slug = "g3-unknown-in-equation"
    grade = 3
    domain = _DOMAIN
    title = "Unknown in a x/÷ equation"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 6 if level <= 1 else (10 if level == 2 else 12)
        a, b = rng.randint(2, hi), rng.randint(2, hi)
        product = a * b
        form = rng.randint(0, 3)
        if form == 0:  # a × ? = product
            prompt = f"{a} × ? = {product}"
            answer = b
        elif form == 1:  # ? × b = product
            prompt = f"? × {b} = {product}"
            answer = a
        elif form == 2:  # ? ÷ a = b  -> product
            prompt = f"? ÷ {a} = {b}"
            answer = product
        else:  # product ÷ ? = b -> a
            prompt = f"{product} ÷ ? = {b}"
            answer = a
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"a": a, "b": b, "product": product, "form": form},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "When part of a multiply or divide equation is missing, use the fact family. "
                "7 × ? = 42 is the same as 42 ÷ 7 = ?, so the missing number is 6. "
                "Multiplication and division undo each other."
            ),
            strategy="Missing factor? Divide. Missing product or dividend? Multiply.",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b, form = problem.payload["a"], problem.payload["b"], problem.payload["form"]
        product = problem.payload["product"]
        if form in (0, 1):
            known = a if form == 0 else b
            return [
                f"Ask: {known} times what makes {product}?",
                f"Use the opposite operation: {product} ÷ {known}.",
            ]
        if form == 2:
            return [
                f"The blank divided by {a} gives {b}, so multiply back.",
                f"Compute {a} × {b} to fill the blank.",
            ]
        return [
            f"{product} divided by the blank gives {b}.",
            f"Ask: {product} ÷ {b} = ?",
        ]

    def worked_example(self, problem: Problem) -> str:
        return f"Use the matching fact family. The missing number is {problem.answer.value}."


class PropertiesOfOperations(Skill):
    id = "3.OA.B.5"
    slug = "g3-properties-operations"
    grade = 3
    domain = _DOMAIN
    title = "Properties of operations"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(2, 6), rng.randint(2, 6)
            prompt = f"If {a} × {b} = {a * b}, what is {b} × {a}?"
            answer = a * b
            kind = "commutative"
        elif level == 2:
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            prompt = f"If {a} × {b} = {a * b}, what is {b} × {a}?"
            answer = a * b
            kind = "commutative"
        else:  # distributive: a × c = a × (split1 + split2)
            a = rng.randint(3, 9)
            c = rng.randint(6, 12)
            s1 = rng.randint(2, c - 2)
            s2 = c - s1
            prompt = (
                f"Use the breaking-apart trick: {a} × {c} = ({a} × {s1}) + ({a} × {s2}) = ?"
            )
            answer = a * c
            kind = "distributive"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"kind": kind},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Properties make multiplying easier. Order doesn't matter (commutative): "
                "7 × 5 = 5 × 7 = 35. You can also break a factor apart (distributive): "
                "6 × 8 = (6 × 5) + (6 × 3) = 30 + 18 = 48."
            ),
            strategy="Swap the order, or break a factor into easy parts and add.",
        )

    def hints(self, problem: Problem) -> list[str]:
        if problem.payload["kind"] == "commutative":
            return [
                "Switching the order of the factors does not change the product.",
                "The answer is the same product you were already given.",
            ]
        return [
            "Multiply each part inside the parentheses.",
            "Then add the two products together.",
        ]

    def worked_example(self, problem: Problem) -> str:
        if problem.payload["kind"] == "commutative":
            return f"Order does not matter, so the product is still {problem.answer.value}."
        return f"Multiply each part, then add: total = {problem.answer.value}."


class DivisionAsUnknownFactor(Skill):
    id = "3.OA.B.6"
    slug = "g3-division-unknown-factor"
    grade = 3
    domain = _DOMAIN
    title = "Division as unknown factor"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 6 if level <= 1 else (9 if level == 2 else 12)
        d = rng.randint(2, hi)
        q = rng.randint(2, hi)
        total = q * d
        prompt = f"What times {d} = {total}? (So {total} ÷ {d} = ?)"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(q),
            payload={"d": d, "q": q, "total": total},
        )

    def invariant(self, problem: Problem) -> bool:
        d, q = problem.payload["d"], problem.payload["q"]
        return problem.payload["total"] == d * q and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Every division question is really a missing-factor question. "
                "45 ÷ 9 = ? is the same as 'what times 9 makes 45?' Since 5 × 9 = 45, "
                "the answer is 5. Use the times tables you already know."
            ),
            strategy="To divide, find the missing factor: what times the divisor makes this?",
        )

    def hints(self, problem: Problem) -> list[str]:
        d, total = problem.payload["d"], problem.payload["total"]
        return [
            f"Think of the {d} times table.",
            f"Count up by {d}s until you reach {total}; the number of steps is the answer.",
        ]

    def worked_example(self, problem: Problem) -> str:
        d, q, total = problem.payload["d"], problem.payload["q"], problem.payload["total"]
        return f"{q} × {d} = {total}, so {total} ÷ {d} = {q}."


class FactsWithin100(Skill):
    id = "3.OA.C.7"
    slug = "g3-facts-within-100"
    grade = 3
    domain = _DOMAIN
    title = "Multiply & divide facts within 100"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(0, 5), rng.randint(0, 5)
        elif level == 2:
            a, b = rng.randint(0, 10), rng.randint(0, 10)
        else:
            a, b = rng.randint(2, 10), rng.randint(2, 10)
        if rng.random() < 0.5 or a == 0:  # multiplication (also guards divide-by-zero)
            prompt = f"{a} × {b} = ?"
            answer = a * b
            op = "×"
        else:  # division fact built from a whole product
            product = a * b
            prompt = f"{product} ÷ {a} = ?"
            answer = b
            op = "÷"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"a": a, "b": b, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 100 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Fluent facts to 100 make all of grade-3 math smoother. Practice both "
                "directions: 6 × 7 = 42 and 42 ÷ 6 = 7. Anything times 0 is 0, and anything "
                "times 1 is itself."
            ),
            strategy="Know each fact both ways: a × b and the matching a-division.",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return [
                f"Skip-count by {a}, {b} times.",
                f"Or use a nearby fact and adjust, like {a} × {max(b - 1, 0)} plus {a}.",
            ]
        return [
            f"Ask: what times {a} makes {a * b}?",
            f"Use the matching multiplication fact for {a}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return f"{a} × {b} = {a * b}."
        return f"{a * b} ÷ {a} = {b}, because {a} × {b} = {a * b}."


class TwoStepWordProblems(Skill):
    id = "3.OA.D.8"
    slug = "g3-two-step-word-problems"
    grade = 3
    domain = _DOMAIN
    title = "Two-step word problems"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        name = rng.choice(_KID_NAMES)
        items = rng.choice(_ITEM_NOUNS)
        hi = 5 if level <= 1 else (9 if level == 2 else 10)
        use_multiply = rng.random() < 0.5
        if use_multiply:
            a, b = rng.randint(2, hi), rng.randint(2, hi)
            base = a * b
            if rng.random() < 0.5:  # (a×b) + c
                c = rng.randint(1, 20)
                prompt = (
                    f"{name} buys {a} packs of {items} with {b} in each pack, "
                    f"then finds {c} more {items}. How many {items} in all?"
                )
                answer = base + c
            else:  # (a×b) - c, kept non-negative
                c = rng.randint(1, base)
                prompt = (
                    f"{name} has {a} boxes with {b} {items} in each, "
                    f"then gives away {c} {items}. How many {items} are left?"
                )
                answer = base - c
        else:  # division first: (total ÷ d) then +/- c
            d = rng.randint(2, hi)
            q = rng.randint(2, hi)
            total = q * d
            if rng.random() < 0.5:  # (total ÷ d) + c
                c = rng.randint(1, 15)
                prompt = (
                    f"{name} splits {total} {items} into {d} equal bags, "
                    f"then adds {c} more {items} to one bag. How many {items} are in that bag?"
                )
                answer = q + c
            else:  # (total ÷ d) - c, kept non-negative
                c = rng.randint(1, q)
                prompt = (
                    f"{name} splits {total} {items} into {d} equal bags, "
                    f"then eats {c} {items} from one bag. How many {items} remain in that bag?"
                )
                answer = q - c
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"items": items, "name": name},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Two-step problems need two operations in order. First do the equal-groups "
                "step (multiply or divide), then do the second step (add or subtract). "
                "Find the in-between number first, then finish."
            ),
            strategy="Do step one to get a middle number, then do step two to finish.",
        )

    def hints(self, problem: Problem) -> list[str]:
        return [
            "First handle the equal groups (multiply or divide) to get a middle number.",
            "Then add or subtract as the second step to reach the final answer.",
        ]

    def worked_example(self, problem: Problem) -> str:
        return (
            "Solve the first step to find the middle number, then do the second step. "
            f"The final answer is {problem.answer.value}."
        )


class ArithmeticPatterns(Skill):
    id = "3.OA.D.9"
    slug = "g3-arithmetic-patterns"
    grade = 3
    domain = _DOMAIN
    title = "Arithmetic patterns"
    max_level = 3
    answer_type = "sequence"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            step = rng.choice((2, 5, 10))
            start = step * rng.randint(1, 4)
        elif level == 2:
            step = rng.choice((3, 4, 6))
            start = step * rng.randint(1, 5)
        else:
            step = rng.choice((7, 8, 9))
            start = step * rng.randint(1, 6)
        shown = [start + step * i for i in range(4)]
        nxt = tuple(start + step * i for i in range(4, 7))
        shown_str = ", ".join(str(v) for v in shown)
        prompt = (
            f"This pattern adds {step} each time: {shown_str}, ... "
            f"What are the next 3 numbers?"
        )
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=SequenceAnswer(nxt),
            payload={"start": start, "step": step, "shown": tuple(shown)},
        )

    def invariant(self, problem: Problem) -> bool:
        return all(v >= 0 for v in problem.answer.values) and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Patterns follow a rule. A skip-counting pattern adds the same number each "
                "step: 5, 10, 15, 20 adds 5. Find the step by subtracting one term from the "
                "next, then keep adding it to continue the pattern."
            ),
            strategy="Find the constant step, then keep adding it to extend the pattern.",
        )

    def hints(self, problem: Problem) -> list[str]:
        step = problem.payload["step"]
        return [
            f"Each number is {step} more than the one before it.",
            f"Keep adding {step} three more times to get the next 3 numbers.",
        ]

    def worked_example(self, problem: Problem) -> str:
        step = problem.payload["step"]
        last = problem.payload["shown"][-1]
        nxt = problem.answer.values
        return (
            f"Add {step} each time starting from {last}: "
            f"{nxt[0]}, {nxt[1]}, {nxt[2]}."
        )


register(MeaningOfMultiplication())
register(MeaningOfDivision())
register(MulDivWordProblems())
register(UnknownInEquation())
register(PropertiesOfOperations())
register(DivisionAsUnknownFactor())
register(FactsWithin100())
register(TwoStepWordProblems())
register(ArithmeticPatterns())
