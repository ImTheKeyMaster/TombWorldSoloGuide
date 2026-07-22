#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ShootingAttackProfileCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()
        cls.css = (ROOT / "styles.css").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_attack_card_is_immediately_before_unchanged_defense_card(self):
        screen = self.source("function showSharedCombatResolutionScreen", "function displaySharedCombatResult")
        attack_card = "${attackLabel?`<div><small>Attack</small><strong>${escapeHtml(attackLabel)}</strong></div>`:''}"
        defense_card = '<div><small>Defense</small><strong>${escapeHtml(defenseLabel)}</strong></div>'
        self.assertIn(attack_card, screen)
        self.assertIn(defense_card, screen)
        self.assertLess(screen.index(attack_card), screen.index(defense_card))
        self.assertNotIn("Ballistic skill", screen)

    def test_shooting_card_uses_the_selected_authoritative_weapon_profile(self):
        resolution = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        self.assertIn("const weapon=playerAttackWeapons(stage.playerOperativeId,attackType)[weaponIndex]", resolution)
        self.assertIn("const profile=playerWeaponProfile(weapon)", resolution)
        self.assertIn("attackLabel:attackType==='shoot'?`${profile.dice} dice · ${profile.hit}+`:''", resolution)
        self.assertNotRegex(resolution, r"attackLabel:.*`4 dice · 3\+`")
        self.assertIn("defenseLabel:`${Math.max(0,3-profile.ap)} dice · ${target.save}+`", resolution)

    def test_weapon_selection_and_dice_resolution_keep_using_the_same_profile(self):
        wizard = self.source("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        resolution = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        automatic_rolls = self.source("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("Number(weaponSelect.value)||0", wizard)
        self.assertIn("runAutomaticCombatRolls({container:screen.dice,profile", resolution)
        self.assertIn("rolledCombatDice(profile.dice,profile.hit,profile.critThreshold)", automatic_rolls)
        dice_roller = self.source("function rolledCombatDice", "function retainedDiceTotals")
        self.assertIn("Array.from({length:Math.max(0,count)}", dice_roller)
        self.assertIn("value>=threshold", dice_roller)

    def test_mobile_grid_preserves_attack_then_defense_without_horizontal_overflow(self):
        self.assertIn(".compact-combat-profile.has-attack-profile{grid-template-columns:repeat(6,minmax(0,1fr))}", self.css)
        self.assertIn(
            ".compact-combat-profile,.compact-combat-profile.has-attack-profile"
            "{grid-template-columns:repeat(2,minmax(0,1fr))}",
            self.css,
        )
        self.assertIn(
            ".compact-combat-profile,.compact-combat-profile.has-attack-profile"
            "{grid-template-columns:repeat(4,minmax(0,1fr))}",
            self.css,
        )
        self.assertIn("width:calc(100% - 16px)", self.css)

    def test_combat_resolution_logic_remains_unchanged(self):
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        self.assertIn("resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile)", preview)
        self.assertIn("result.attackDice=result.rolledAttackDice", preview)
        self.assertIn("result.saveDice=result.rolledDefenseDice", preview)
        self.assertIn("result.retainedSaves=retainedDiceTotals(result.saveDice)", preview)


if __name__ == "__main__":
    unittest.main()
