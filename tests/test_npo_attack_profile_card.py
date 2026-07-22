#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NpoAttackProfileCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()
        cls.css = (ROOT / "styles.css").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_shared_attack_card_is_immediately_before_defense(self):
        screen = self.source("function showSharedCombatResolutionScreen", "function displaySharedCombatResult")
        attack = "${attackLabel?`<div><small>Attack</small><strong>${escapeHtml(attackLabel)}</strong></div>`:''}"
        defense = '<div><small>Defense</small><strong>${escapeHtml(defenseLabel)}</strong></div>'
        self.assertIn(attack, screen)
        self.assertLess(screen.index(attack), screen.index(defense))

    def test_npo_shooting_and_melee_use_the_selected_attack_profile(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("const attackType=state.lastActivation?.action?.includes('Fight')?'melee':'shoot'", wizard)
        self.assertIn("const availableProfiles=npoAttackProfiles(n,attackType)", wizard)
        self.assertIn("attackLabel:combatAttackLabel(initialProfile)", wizard)
        self.assertIn("profile=canonicalAttackProfile(availableProfiles[Number($('#npoCombatProfile')?.value)||0])", wizard)
        self.assertIn("attack.textContent=combatAttackLabel(profile)", wizard)
        self.assertNotRegex(wizard, r"attackLabel:`[0-9]+ dice")

    def test_display_and_roll_share_authoritative_dice_and_hit_values(self):
        formatter = self.source("function combatAttackLabel", "function showSharedCombatResolutionScreen")
        roller = self.source("function runAutomaticCombatRolls", "function retainedDiceTotals")
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("profile.dice", formatter)
        self.assertIn("profile.hit", formatter)
        self.assertIn("rolledCombatDice(profile.dice,profile.hit,profile.critThreshold)", roller)
        self.assertIn("runAutomaticCombatRolls({container:screen.dice,profile", wizard)
        self.assertIn("defenseLabel:`3 dice · ${target.save||3}+`", wizard)

    def test_weapon_changes_refresh_attack_and_rules_without_changing_resolution(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("$('#npoCombatProfile')?.addEventListener('change',startAutomaticCombat)", wizard)
        self.assertIn("resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile)", wizard)
        self.assertIn("applyNpoAttackDamage(n,target,summary)", wizard)
        self.assertIn("if(resolutionCommitted)return", wizard)

    def test_profile_grid_is_responsive_without_empty_cells(self):
        self.assertIn(".compact-combat-profile.has-attack-profile{grid-template-columns:repeat(6,minmax(0,1fr))}", self.css)
        self.assertIn(".compact-combat-profile,.compact-combat-profile.has-attack-profile{grid-template-columns:repeat(2,minmax(0,1fr))}", self.css)
        self.assertIn(".compact-combat-profile,.compact-combat-profile.has-attack-profile{grid-template-columns:1fr}", self.css)
        self.assertIn("width:calc(100% - 16px)", self.css)


if __name__ == "__main__":
    unittest.main()
