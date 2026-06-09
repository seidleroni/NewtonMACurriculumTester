"""Grade 4 Operations & Algebraic Thinking skills."""

from __future__ import annotations

import random

from mathkids.answers import IntegerAnswer, WordAnswer
from mathkids.engine.base import Lesson, Problem, Skill, register, shuffled_mc

_DOMAIN = "Operations & Algebraic Thinking"

_KID_NAMES = ("Mia", "Leo", "Ava", "Sam", "Zoe", "Jack", "Nina", "Eli")
_ITEM_NOUNS = ("apples", "marbles", "stickers", "cookies", "crayons", "pencils", "books")
_LONG_UNITS = ("inches", "feet", "meters", "centimeters")
_LONG_THINGS = ("ribbon", "rope", "string", "trail", "ladder", "fence")


def _factors(n: int) -> frozenset[int]:
    out: set[int] = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.add(i)
            out.add(n // i)
        i += 1
    return frozenset(out)


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


class FactsTo12(Skill):
    id = "4.OA.A.3.a"
    slug = "g4-facts-to-12"
    grade = 4
    domain = _DOMAIN
    title = "Multiplication & division facts to 12 × 12"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        if level <= 1:
            a, b = rng.randint(1, 9), rng.randint(1, 9)
            prompt, ans, op = f"{a} × {b} = ?", a * b, "×"
        elif level == 2:
            a, b = rng.randint(1, 12), rng.randint(1, 12)
            prompt, ans, op = f"{a} × {b} = ?", a * b, "×"
        else:  # division facts, built from a whole product (divisor never 0)
            a, b = rng.randint(2, 12), rng.randint(1, 12)
            product = a * b
            prompt, ans, op = f"{product} ÷ {a} = ?", b, "÷"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(ans),
            payload={"a": a, "b": b, "op": op},
        )

    def invariant(self, problem: Problem) -> bool:
        return 0 <= problem.answer.value <= 144 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Knowing the times tables all the way to 12 × 12 makes everything else faster. "
                "Division is the flip side of multiplication: 56 ÷ 8 asks 'what times 8 makes "
                "56?', so the answer is 7 because 7 × 8 = 56."
            ),
            strategy="Dividing? Ask: what number times the divisor makes this total?",
        )

    def hints(self, problem: Problem) -> list[str]:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return [
                f"Skip-count by {a}, a total of {b} times.",
                f"Or use a nearby fact: {a} × {b} is {a} × {max(b - 1, 0)} plus {a}.",
            ]
        return [
            f"Ask: what number times {a} makes {a * b}?",
            f"Count up {a}, {a * 2}, {a * 3}, … until you reach {a * b}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        a, b, op = problem.payload["a"], problem.payload["b"], problem.payload["op"]
        if op == "×":
            return f"{a} × {b} = {a * b}."
        return f"{a * b} ÷ {a}: since {a} × {b} = {a * b}, the answer is {b}."


class MultiplicativeComparison(Skill):
    id = "4.OA.A.1"
    slug = "g4-multiplicative-comparison"
    grade = 4
    domain = _DOMAIN
    title = "Multiplicative comparison"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 6 if level <= 1 else (10 if level == 2 else 12)
        n = rng.randint(2, hi)
        b = rng.randint(2, hi)
        product = n * b
        who, other = rng.sample(_KID_NAMES, 2)
        items = rng.choice(_ITEM_NOUNS)
        find_product = level <= 1 or rng.random() < 0.5
        if find_product:  # other has b, who has n times as many -> find who's count
            prompt = (
                f"{other} has {b} {items}. {who} has {n} times as many {items} "
                f"as {other}. How many {items} does {who} have?"
            )
            answer = product
            mode = "product"
        else:  # who has n*b, other has b -> find how many times as many
            prompt = (
                f"{who} has {product} {items} and {other} has {b} {items}. "
                f"How many times as many {items} does {who} have as {other}?"
            )
            answer = n
            mode = "factor"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={
                "n": n, "b": b, "product": product, "mode": mode,
                "who": who, "other": other, "items": items,
            },
        )

    def invariant(self, problem: Problem) -> bool:
        n, b, product = problem.payload["n"], problem.payload["b"], problem.payload["product"]
        return product == n * b and problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "'Times as many' is a multiplication comparison. '15 is 3 times as many as 5' "
                "means 15 = 3 × 5. If you know the small number and how many times, multiply to "
                "find the big number. If you know both totals, divide to find how many times."
            ),
            strategy="Big number = (times) × (small number). Missing the times? Divide.",
        )

    def hints(self, problem: Problem) -> list[str]:
        n, b = problem.payload["n"], problem.payload["b"]
        who = problem.payload["who"]
        if problem.payload["mode"] == "product":
            return [
                f"'{n} times as many as {b}' means {n} groups of {b}.",
                f"Multiply: {n} × {b}.",
            ]
        return [
            f"Ask: {b} times what equals {problem.payload['product']}?",
            f"Divide {who}'s amount by {b}: {problem.payload['product']} ÷ {b}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n, b, product = problem.payload["n"], problem.payload["b"], problem.payload["product"]
        who = problem.payload["who"]
        if problem.payload["mode"] == "product":
            return f"{n} times as many as {b} is {n} × {b} = {product}, so {who} has {product}."
        return f"{product} ÷ {b} = {n}, so {who} has {n} times as many."


class ComparisonWordProblems(Skill):
    id = "4.OA.A.2"
    slug = "g4-comparison-word-problems"
    grade = 4
    domain = _DOMAIN
    title = "Multiplicative comparison word problems"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 6 if level <= 1 else (10 if level == 2 else 12)
        n = rng.randint(2, hi)
        k = rng.randint(2, hi)
        unit = rng.choice(_LONG_UNITS)
        big_thing = rng.choice(_LONG_THINGS)
        small_thing = rng.choice([t for t in _LONG_THINGS if t != big_thing])
        do_multiply = level <= 1 or rng.random() < 0.5
        if do_multiply:  # short = k, big is n times as long -> find big
            big = n * k
            prompt = (
                f"The {small_thing} is {k} {unit} long. "
                f"The {big_thing} is {n} times as long as the {small_thing}. "
                f"How long is the {big_thing}, in {unit}?"
            )
            answer = big
            mode = "multiply"
        else:  # big = n*k known, big is n times as long -> find short
            big = n * k
            prompt = (
                f"The {big_thing} is {big} {unit} long. "
                f"That is {n} times as long as the {small_thing}. "
                f"How long is the {small_thing}, in {unit}?"
            )
            answer = k
            mode = "divide"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload={"n": n, "k": k, "mode": mode},
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value > 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "These word problems compare two lengths with 'times as long'. If you know the "
                "short length and how many times longer the other is, multiply. If you know the "
                "long length and how many times it is, divide to find the short one."
            ),
            strategy="Finding the longer thing? Multiply. Finding the shorter thing? Divide.",
        )

    def hints(self, problem: Problem) -> list[str]:
        n = problem.payload["n"]
        if problem.payload["mode"] == "multiply":
            return [
                f"The longer one is {n} times the shorter one.",
                f"Multiply the short length by {n}.",
            ]
        return [
            f"The long length is {n} equal parts.",
            f"Divide the long length by {n} to get one part (the short length).",
        ]

    def worked_example(self, problem: Problem) -> str:
        n, k = problem.payload["n"], problem.payload["k"]
        if problem.payload["mode"] == "multiply":
            return f"{n} times as long as {k} is {n} × {k} = {n * k}."
        return f"{n * k} split into {n} equal parts is {n * k} ÷ {n} = {k}."


class MultiStepRemainders(Skill):
    id = "4.OA.A.3"
    slug = "g4-multistep-remainders"
    grade = 4
    domain = _DOMAIN
    title = "Multi-step + interpret remainders"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        name = rng.choice(_KID_NAMES)
        items = rng.choice(_ITEM_NOUNS)
        kind = rng.choice(("buses", "combine"))
        if kind == "buses":  # round UP: each group needs a whole container
            cap = rng.choice((4, 6, 8, 10, 12))
            if level <= 1:
                people = rng.randint(cap + 1, cap * 4)
            elif level == 2:
                people = rng.randint(cap + 1, cap * 7)
            else:
                people = rng.randint(cap + 1, cap * 12)
            buses = -(-people // cap)  # ceiling division
            prompt = (
                f"{people} students are going on a trip. Each bus holds {cap} students. "
                f"How many buses are needed so everyone has a seat?"
            )
            answer = buses
            payload = {"kind": "buses", "people": people, "cap": cap}
        else:  # (a × b) - c, kept non-negative
            hi = 6 if level <= 1 else (9 if level == 2 else 12)
            a, b = rng.randint(2, hi), rng.randint(2, hi)
            base = a * b
            c = rng.randint(1, base)
            prompt = (
                f"{name} has {a} boxes with {b} {items} in each box, "
                f"then gives away {c} {items}. How many {items} are left?"
            )
            answer = base - c
            payload = {"kind": "combine", "a": a, "b": b, "c": c}
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(answer),
            payload=payload,
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["kind"] == "buses":
            need = -(-p["people"] // p["cap"])
            ok = problem.answer.value == need and (need - 1) * p["cap"] < p["people"]
        else:
            ok = problem.answer.value == p["a"] * p["b"] - p["c"]
        return ok and problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "Multi-step problems take more than one operation, and you must read what the "
                "remainder means. If everyone needs a seat, a leftover group still needs one "
                "more bus, so you round UP. Other times you multiply equal groups first, then "
                "add or take away."
            ),
            strategy="Leftover people still need a bus? Round up. Otherwise do each step in order.",
        )

    def hints(self, problem: Problem) -> list[str]:
        p = problem.payload
        if p["kind"] == "buses":
            return [
                f"Divide {p['people']} by {p['cap']} to see how many full buses there are.",
                "If any students are left over, add one more bus so everyone fits.",
            ]
        return [
            f"First multiply the equal groups: {p['a']} × {p['b']}.",
            f"Then subtract the {p['c']} given away.",
        ]

    def worked_example(self, problem: Problem) -> str:
        p = problem.payload
        if p["kind"] == "buses":
            people, cap = p["people"], p["cap"]
            full = people // cap
            left = people % cap
            buses = -(-people // cap)
            if left:
                return (
                    f"{people} ÷ {cap} = {full} remainder {left}. The {left} leftover students "
                    f"still need a bus, so round up to {buses} buses."
                )
            return f"{people} ÷ {cap} = {full} exactly, so {buses} buses are needed."
        a, b, c = p["a"], p["b"], p["c"]
        return f"{a} × {b} = {a * b}, then {a * b} - {c} = {a * b - c}."


class FactorsMultiplesPrimes(Skill):
    id = "4.OA.B.4"
    slug = "g4-factors-multiples-primes"
    grade = 4
    domain = _DOMAIN
    title = "Factors, multiples, prime/composite"
    max_level = 3
    answer_type = "multiple_choice"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        hi = 24 if level <= 1 else (40 if level == 2 else 60)
        do_factors = rng.random() < 0.5
        if do_factors:  # pick the one true factor of n among four choices
            f = rng.randint(2, 9)
            m = rng.randint(2, max(2, hi // f))
            n = f * m
            non_divisors = [d for d in range(2, 13) if n % d != 0]
            distractors = tuple(str(d) for d in rng.sample(non_divisors, 3))
            prompt = f"Which of these is a factor of {n}?"
            return Problem(
                skill_id=self.id,
                level=level,
                prompt=prompt,
                answer=shuffled_mc(rng, str(f), distractors),
                payload={"variant": "factor_mc", "n": n, "f": f},
            )
        # prime vs composite (n >= 2 so the question is well-posed)
        n = rng.randint(2, hi)
        label = "prime" if _is_prime(n) else "composite"
        prompt = f"Is {n} prime or composite?"
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=WordAnswer(label),
            payload={"variant": "primecheck", "n": n, "label": label},
        )

    def invariant(self, problem: Problem) -> bool:
        p = problem.payload
        if p["variant"] == "factor_mc":
            n = p["n"]
            opts = problem.answer.options
            correct = int(opts[problem.answer.correct_index])
            others_wrong = all(
                n % int(o) != 0
                for i, o in enumerate(opts)
                if i != problem.answer.correct_index
            )
            return n % correct == 0 and others_wrong and super().invariant(problem)
        n = p["n"]
        expect = "prime" if _is_prime(n) else "composite"
        return p["label"] == expect and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A factor of a number divides it evenly with no remainder. Factors come in "
                "pairs: for 12, 1×12, 2×6, and 3×4 give factors 1, 2, 3, 4, 6, 12. A prime "
                "number has exactly two factors (1 and itself); a composite number has more "
                "than two."
            ),
            strategy="Test 1, 2, 3, … for even division. Exactly two factors? Prime.",
        )

    def hints(self, problem: Problem) -> list[str]:
        n = problem.payload["n"]
        if problem.payload["variant"] == "factor_mc":
            return [
                f"A factor divides {n} evenly, with no remainder.",
                f"Try dividing {n} by each choice — only one leaves no remainder.",
            ]
        return [
            f"Can any number besides 1 and {n} divide {n} evenly?",
            "If yes, it is composite; if the only factors are 1 and itself, it is prime.",
        ]

    def worked_example(self, problem: Problem) -> str:
        n = problem.payload["n"]
        if problem.payload["variant"] == "factor_mc":
            f = problem.payload["f"]
            return f"{n} ÷ {f} = {n // f} with no remainder, so {f} is a factor of {n}."
        label = problem.payload["label"]
        if label == "prime":
            return f"{n} has only the factors 1 and {n}, so {n} is prime."
        facs = sorted(_factors(n))
        other = facs[1]  # smallest factor greater than 1
        return f"{n} can be divided by {other} ({n} ÷ {other} = {n // other}), so {n} is composite."


class GeneratePatterns(Skill):
    id = "4.OA.C.5"
    slug = "g4-generate-patterns"
    grade = 4
    domain = _DOMAIN
    title = "Generate & analyze patterns"
    max_level = 3
    answer_type = "integer"
    phase = 1

    def generate(self, level: int, rng: random.Random) -> Problem:
        use_multiply = level >= 3 and rng.random() < 0.5
        if use_multiply:  # multiply by k each time
            k = rng.choice((2, 3))
            start = rng.randint(1, 4)
            terms = [start]
            for _ in range(3):
                terms.append(terms[-1] * k)
            nxt = terms[-1] * k
            rule = f"multiply by {k}"
            payload = {"op": "multiply", "k": k, "start": start}
        else:  # add k each time
            if level <= 1:
                k = rng.choice((2, 5, 10))
            elif level == 2:
                k = rng.choice((3, 4, 6, 7))
            else:
                k = rng.choice((8, 9, 11, 12))
            start = rng.randint(1, 9)
            terms = [start + k * i for i in range(4)]
            nxt = terms[-1] + k
            rule = f"add {k}"
            payload = {"op": "add", "k": k, "start": start}
        shown = ", ".join(str(v) for v in terms)
        prompt = f"The rule is '{rule}'. The pattern starts {shown}, ___. What is the next number?"
        payload["shown"] = tuple(terms)
        return Problem(
            skill_id=self.id,
            level=level,
            prompt=prompt,
            answer=IntegerAnswer(nxt),
            payload=payload,
        )

    def invariant(self, problem: Problem) -> bool:
        return problem.answer.value >= 0 and super().invariant(problem)

    def lesson(self) -> Lesson:
        return Lesson(
            title=self.title,
            body=(
                "A pattern follows a rule applied to each term to get the next. An 'add' rule "
                "increases by the same amount every step (2, 5, 8, 11 adds 3). A 'multiply' rule "
                "scales each term (1, 2, 4, 8 multiplies by 2). Apply the rule again to extend it."
            ),
            strategy="Apply the same rule to the last term, over and over, to continue.",
        )

    def hints(self, problem: Problem) -> list[str]:
        op, k = problem.payload["op"], problem.payload["k"]
        if op == "add":
            return [
                f"Each number is {k} more than the one before it.",
                f"Add {k} to the last number in the pattern.",
            ]
        return [
            f"Each number is {k} times the one before it.",
            f"Multiply the last number in the pattern by {k}.",
        ]

    def worked_example(self, problem: Problem) -> str:
        op, k = problem.payload["op"], problem.payload["k"]
        last = problem.payload["shown"][-1]
        nxt = problem.answer.value
        if op == "add":
            return f"Add {k} to the last number: {last} + {k} = {nxt}."
        return f"Multiply the last number by {k}: {last} × {k} = {nxt}."


register(FactsTo12())
register(MultiplicativeComparison())
register(ComparisonWordProblems())
register(MultiStepRemainders())
register(FactorsMultiplesPrimes())
register(GeneratePatterns())
