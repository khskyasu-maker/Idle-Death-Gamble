import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

from machine_traits import machine_has_lt, machine_has_upper  # noqa: E402
from machines import MACHINES  # noqa: E402
from machines import Machine, Payout  # noqa: E402
from model_checks import validate_all_machine_models, validate_machine_model  # noqa: E402
from result_formatting import build_ascii_table, minutes_text, yen  # noqa: E402
from result_output_helpers import (  # noqa: E402
    benchmark_model_value,
    fall_state_continue_chance,
)
from spec_benchmarks import PUBLIC_BENCHMARKS  # noqa: E402
from stores import (  # noqa: E402
    ACTIVE_EVA_SIM_MODEL_IDS,
    ACTIVE_OTHER_SIM_MODEL_IDS,
    MACHINE_NAME_TO_SIM_ID,
    STORE_INVENTORY,
    store_contexts_for_machine,
)


class SimulatorSpecTests(unittest.TestCase):
    def test_all_machine_models_validate(self):
        self.assertEqual([], validate_all_machine_models(MACHINES))

    def test_public_benchmarks_stay_close_to_model_values(self):
        issues = []
        for machine_id, benchmarks in PUBLIC_BENCHMARKS.items():
            machine = MACHINES[machine_id]
            for benchmark in benchmarks:
                model_value = benchmark_model_value(machine, benchmark)
                public_value = float(benchmark["public"])
                tolerance = 0.5 if benchmark["unit"] == "denom" else 3.0
                if abs(model_value - public_value) > tolerance:
                    issues.append(
                        f"{machine_id} {benchmark['label_ja']}: "
                        f"public={public_value}, model={model_value:.2f}"
                    )
        self.assertEqual([], issues)

    def test_non_lt_upper_rush_is_not_counted_as_lt(self):
        machine = MACHINES["sea_5_black_199"]
        self.assertFalse(machine_has_lt(machine))
        self.assertTrue(machine_has_upper(machine))
        self.assertAlmostEqual(
            0.0,
            sum(p.weight for p in machine.st_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.04,
            sum(p.weight for p in machine.st_hit_dist if p.next_state == "UPPER"),
        )

    def test_core_lt_machine_step_specs(self):
        sea_black_lt = MACHINES["sea_5_black_lt"]
        self.assertTrue(machine_has_lt(sea_black_lt))
        self.assertEqual([310, 310], [p.balls for p in sea_black_lt.normal_hit_dist])
        self.assertAlmostEqual(
            0.70,
            sum(p.weight for p in sea_black_lt.normal_hit_dist if p.next_state == "ST"),
        )
        self.assertAlmostEqual(
            0.10,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.40,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.balls == 820),
        )
        self.assertAlmostEqual(
            0.60,
            sum(p.weight for p in sea_black_lt.st_hit_dist if p.balls == 310),
        )

        shin_eva_lt = MACHINES["shin_eva_129_lt"]
        self.assertAlmostEqual(
            0.005,
            sum(p.weight for p in shin_eva_lt.normal_hit_dist if p.next_state == "LT"),
        )
        self.assertAlmostEqual(
            0.10,
            sum(p.weight for p in shin_eva_lt.st_hit_dist if p.next_state == "LT"),
        )

    def test_lt_state_models_must_define_lt_distribution(self):
        broken = Machine(
            id="broken_lt",
            name_ja="壊れたLT",
            name_ko="깨진 LT",
            spec_type="test LT",
            risk_grade="test",
            normal_prob=99.9,
            high_prob=50.0,
            normal_hit_dist=[Payout(balls=300, weight=1.0, next_state="LT")],
            st_hit_dist=[],
            jitan_hit_dist=[],
            kakuben_hit_dist=[],
            lt_hit_dist=[],
        )
        issues = validate_machine_model(broken)
        self.assertIn("broken_lt.normal_hit_dist[0]: LT state transitions must set is_lt=True", issues)
        self.assertIn("broken_lt: LT state transitions require lt_hit_dist", issues)

    def test_eva15_319_uses_practical_vst_outputs(self):
        eva15 = MACHINES["eva_15_roar"]
        self.assertEqual([1400, 420, 420], [p.balls for p in eva15.normal_hit_dist])
        self.assertEqual([0.03, 0.56, 0.41], [p.weight for p in eva15.normal_hit_dist])
        self.assertEqual(["ST", "ST", "JITAN"], [p.next_state for p in eva15.normal_hit_dist])
        self.assertEqual([True, True, False], [p.counts_as_rush for p in eva15.normal_hit_dist])
        self.assertEqual({163}, {p.st_spins for p in eva15.normal_hit_dist if p.next_state == "ST"})
        self.assertEqual({100}, {p.jitan_spins for p in eva15.normal_hit_dist if p.next_state == "JITAN"})
        self.assertEqual([1400], [p.balls for p in eva15.st_hit_dist])
        self.assertEqual([1400], [p.balls for p in eva15.jitan_hit_dist])

        mediterranean = MACHINES["mediterranean_2_89"]
        self.assertEqual({24}, {p.st_spins for p in mediterranean.normal_hit_dist})
        self.assertEqual(
            {48, 100},
            {p.st_spins for p in mediterranean.st_hit_dist},
        )
        self.assertEqual({104}, {p.st_spins for p in mediterranean.lt_hit_dist})

        re_zero_s2_129 = MACHINES["re_zero_s2_129"]
        self.assertTrue(machine_has_lt(re_zero_s2_129))
        self.assertFalse(any(p.next_state == "LT" for p in re_zero_s2_129.st_hit_dist))
        self.assertAlmostEqual(
            0.125,
            sum(p.weight for p in re_zero_s2_129.st_hit_dist if p.is_lt),
        )

    def test_remaining_eva_models_use_practical_outputs(self):
        expectations = {
            "eva_15_premium": ([930, 280, 280], [930, 280], [930, 280]),
            "shin_eva_premium_99": ([930, 280, 280], [930, 280], [930, 280]),
            "shin_eva_type_rei": ([1400, 280, 280], [1400], [1400]),
            "eva_15_special_199": ([1020, 300, 300], [1020], [1020]),
            "shin_eva_129_lt": ([930, 280, 280], [930, 930], []),
        }
        for machine_id, (normal_balls, st_balls, jitan_balls) in expectations.items():
            with self.subTest(machine_id=machine_id):
                machine = MACHINES[machine_id]
                self.assertEqual(normal_balls, [p.balls for p in machine.normal_hit_dist])
                self.assertEqual(st_balls, [p.balls for p in machine.st_hit_dist])
                self.assertEqual(jitan_balls, [p.balls for p in machine.jitan_hit_dist])
                self.assertTrue(all(p.ball_variance == 0.03 for p in machine.normal_hit_dist))

        eva_beginning = MACHINES["eva_beginning"]
        self.assertTrue(machine_has_lt(eva_beginning))
        self.assertAlmostEqual(349.9, eva_beginning.normal_prob)
        self.assertAlmostEqual(399.9, eva_beginning.jitan_prob)
        self.assertEqual([1400, 280, 280], [p.balls for p in eva_beginning.normal_hit_dist])
        self.assertEqual(["LT", "LT", "JITAN"], [p.next_state for p in eva_beginning.normal_hit_dist])
        self.assertEqual([True, True, False], [p.counts_as_rush for p in eva_beginning.normal_hit_dist])
        self.assertEqual([], eva_beginning.st_hit_dist)
        self.assertEqual([280], [p.balls for p in eva_beginning.jitan_hit_dist])
        self.assertEqual([4480, 2240], [p.balls for p in eva_beginning.lt_hit_dist])

        shin_eva_lt = MACHINES["shin_eva_129_lt"]
        self.assertEqual([True, True, False], [p.counts_as_rush for p in shin_eva_lt.normal_hit_dist])

    def test_additional_sea_models_match_public_step_specs(self):
        sea5 = MACHINES["sea_5"]
        self.assertEqual(["KAKUBEN", "JITAN"], [p.next_state for p in sea5.normal_hit_dist])
        self.assertEqual([True, False], [p.counts_as_rush for p in sea5.normal_hit_dist])
        self.assertEqual({100}, {p.jitan_spins for p in sea5.normal_hit_dist if p.next_state == "JITAN"})

        sea5_special = MACHINES["sea_5_special"]
        self.assertEqual([0.54, 0.46], [p.weight for p in sea5_special.normal_hit_dist])
        self.assertEqual({100}, {p.jitan_spins for p in sea5_special.normal_hit_dist if p.next_state == "JITAN"})
        self.assertEqual({200}, {p.jitan_spins for p in sea5_special.jitan_hit_dist if p.next_state == "JITAN"})

        sea5_agnes = MACHINES["sea_5_agnes"]
        self.assertEqual([1000, 600, 400, 400], [p.balls for p in sea5_agnes.normal_hit_dist])
        self.assertEqual("UPPER", sea5_agnes.normal_hit_dist[0].next_state)
        self.assertEqual([10], sorted({p.st_spins for p in sea5_agnes.normal_hit_dist}))
        self.assertEqual([15, 40, 110], sorted({p.jitan_spins for p in sea5_agnes.normal_hit_dist}))
        self.assertEqual(
            [p.jitan_spins for p in sea5_agnes.normal_hit_dist],
            [p.jitan_spins for p in sea5_agnes.jitan_hit_dist],
        )
        self.assertEqual([1000, 600, 400], [p.balls for p in sea5_agnes.upper_hit_dist])
        self.assertEqual({110}, {p.jitan_spins for p in sea5_agnes.upper_hit_dist})

        black4 = MACHINES["sea_4_special_black"]
        self.assertEqual([1400, 700, 420], [p.balls for p in black4.normal_hit_dist])
        self.assertAlmostEqual(0.30, black4.normal_hit_dist[0].weight)
        self.assertAlmostEqual(0.30, black4.normal_hit_dist[1].weight)
        self.assertAlmostEqual(0.40, black4.normal_hit_dist[2].weight)
        self.assertEqual({51}, {p.st_spins for p in black4.st_hit_dist})

        sea3r3 = MACHINES["sea_3r3"]
        self.assertAlmostEqual(
            0.51,
            sum(p.weight for p in sea3r3.normal_hit_dist if p.next_state == "KAKUBEN"),
        )
        self.assertAlmostEqual(
            0.49,
            sum(p.weight for p in sea3r3.normal_hit_dist if p.next_state == "JITAN"),
        )
        self.assertEqual({40}, {p.jitan_spins for p in sea3r3.normal_hit_dist if p.next_state == "JITAN"})

        extreme = MACHINES["sea_extreme_japan"]
        self.assertEqual([True, False], [p.counts_as_rush for p in extreme.normal_hit_dist])
        self.assertEqual({24, 104}, {p.st_spins for p in extreme.normal_hit_dist})
        self.assertAlmostEqual(0.20, sum(p.weight for p in extreme.st_hit_dist if p.balls == 3000))
        self.assertAlmostEqual(0.55, sum(p.weight for p in extreme.st_hit_dist if p.balls == 1500))
        self.assertAlmostEqual(0.25, sum(p.weight for p in extreme.st_hit_dist if p.balls == 300))

        naginami = MACHINES["sea_extreme_japan_naginami"]
        self.assertEqual({20, 74}, {p.st_spins for p in naginami.normal_hit_dist})
        self.assertAlmostEqual(0.05, sum(p.weight for p in naginami.st_hit_dist if p.balls == 1600))
        self.assertAlmostEqual(0.70, sum(p.weight for p in naginami.st_hit_dist if p.balls == 800))
        self.assertAlmostEqual(0.25, sum(p.weight for p in naginami.st_hit_dist if p.balls == 240))

    def test_other_candidate_models_match_public_step_specs(self):
        lupin = MACHINES["lupin_77_sweet"]
        self.assertEqual([210, 210], [p.balls for p in lupin.normal_hit_dist])
        self.assertEqual(["ST", "NORMAL"], [p.next_state for p in lupin.normal_hit_dist])
        self.assertEqual({34}, {p.st_spins for p in lupin.normal_hit_dist if p.next_state == "ST"})
        self.assertAlmostEqual(0.15, sum(p.weight for p in lupin.st_hit_dist if p.next_state == "LT"))
        self.assertEqual({88}, {p.st_spins for p in lupin.lt_hit_dist})

        kabaneri = MACHINES["kabaneri_2"]
        self.assertTrue(machine_has_lt(kabaneri))
        self.assertEqual([700, 700], [p.balls for p in kabaneri.normal_hit_dist])
        self.assertEqual(["LT", "NORMAL"], [p.next_state for p in kabaneri.normal_hit_dist])
        self.assertEqual([5580, 2790, 1400], [p.balls for p in kabaneri.lt_hit_dist])
        self.assertAlmostEqual(0.062, kabaneri.lt_hit_dist[0].weight)
        self.assertEqual({134}, {p.st_spins for p in kabaneri.lt_hit_dist})

        ghoul = MACHINES["tokyo_ghoul"]
        self.assertEqual(199.9, ghoul.normal_prob)
        self.assertEqual([1400, 280, 1400, 280], [p.balls for p in ghoul.normal_hit_dist])
        self.assertAlmostEqual(0.255, sum(p.weight for p in ghoul.normal_hit_dist if p.next_state == "LT"))
        self.assertEqual([5600, 2800], [p.balls for p in ghoul.lt_hit_dist])

        jibo = MACHINES["hokuto_jibo"]
        self.assertEqual([900, 450, 120], [p.balls for p in jibo.normal_hit_dist])
        self.assertEqual({5}, {p.st_spins for p in jibo.normal_hit_dist})
        self.assertEqual({0, 25, 50}, {p.jitan_spins for p in jibo.normal_hit_dist})
        self.assertAlmostEqual(0.010, sum(p.weight for p in jibo.st_hit_dist if p.next_state == "LT"))
        self.assertEqual({166}, {p.jitan_spins for p in jibo.lt_hit_dist})
        self.assertTrue(all(p.next_state == "LT" for p in jibo.lt_hit_dist))

    def test_active_other_subset_is_exact_current_policy(self):
        expected = {
            "hokuto_jibo",
            "re_zero_99",
            "re_zero_s2_129",
            "lupin_77_sweet",
            "kabaneri_2",
            "tokyo_ghoul",
        }
        self.assertEqual(expected, ACTIVE_OTHER_SIM_MODEL_IDS)

        selectable_other_ids = {
            row["id"]
            for store in STORE_INVENTORY.values()
            for row in store["machines"]
            if row["lineup_category"] == "other"
        }
        self.assertEqual(expected, selectable_other_ids)

        inactive_names = {
            "P Re:ゼロから始める異世界生活 鬼がかり 199ver.",
            "e Re:ゼロから始める異世界生活 season2",
            "e北斗の拳10",
        }
        self.assertTrue(inactive_names.isdisjoint(MACHINE_NAME_TO_SIM_ID))

    def test_re_zero_season2_129_is_only_selectable_for_hips_low_rate(self):
        contexts = store_contexts_for_machine("re_zero_s2_129", include_missing=True)
        installed = [context for context in contexts if context["installed"]]

        self.assertEqual(["arrow_namba_hips"], [context["store_id"] for context in installed])
        self.assertEqual([2], [context["count"] for context in installed])
        self.assertEqual(["1yen"], [context["rate"] for context in installed])

    def test_result_formatting_helpers_handle_terminal_output(self):
        table = build_ascii_table(["항목", "값"], [["기종", "e東京喰種"], ["메모", "A|B"]])

        self.assertIn("e東京喰種", table)
        self.assertIn("A/B", table)
        self.assertNotIn("A|B", table)
        self.assertEqual("+1,500yen", yen(1500, signed=True))
        self.assertEqual("1시간 15분", minutes_text(75))

    def test_active_eva_lineup_policy_is_explicit(self):
        expected_active_eva = {
            "eva_15_roar",
            "eva_15_premium",
            "eva_15_special_199",
            "shin_eva_type_rei",
            "shin_eva_premium_99",
            "shin_eva_129_lt",
            "eva_beginning",
        }
        self.assertEqual(expected_active_eva, set(ACTIVE_EVA_SIM_MODEL_IDS))

        supported_eva_ids = {
            row["id"]
            for store in STORE_INVENTORY.values()
            for row in store["machines"]
            if row.get("lineup_category") == "eva"
        }
        self.assertTrue(supported_eva_ids <= expected_active_eva)

        unsupported_eva_names = {
            row["machine_name"]
            for store in STORE_INVENTORY.values()
            for row in store["unsupported_machines"]
            if row.get("lineup_category") == "eva"
        }
        self.assertEqual({"eゴジラ対エヴァンゲリオン2 超デカゴールド"}, unsupported_eva_names)

    def test_hokuto_fall_type_continuation_rates(self):
        hokuto = MACHINES["hokuto_10"]
        self.assertEqual({"ST": 136.9, "LT": 275.9}, hokuto.fall_prob)
        self.assertEqual({"ST": 4, "LT": 4}, hokuto.fall_reserve_spins)
        self.assertAlmostEqual(80.0, fall_state_continue_chance(hokuto, "ST"), delta=0.2)
        self.assertAlmostEqual(89.0, fall_state_continue_chance(hokuto, "LT"), delta=0.3)

if __name__ == "__main__":
    unittest.main()
