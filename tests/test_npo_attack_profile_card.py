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
        self.assertIn("initialProfile?combatAttackLabel(initialProfile):'—'", wizard)
        self.assertIn("profile=canonicalAttackProfile(availableProfiles[profileIndex])", wizard)
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
        self.assertIn("guidance.innerHTML=npoCombatGuidanceHtml(n,{attackType,profile})", wizard)
        self.assertIn("resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile)", wizard)
        self.assertIn("applyNpoAttackDamage(n,target,summary)", wizard)
        self.assertIn("if(resolutionCommitted)return", wizard)

    def test_multiple_profiles_require_a_deliberate_selection_before_rolling(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        placeholder = '<option value="" selected disabled>Select a weapon...</option>'
        self.assertIn(placeholder, wizard)
        self.assertIn("else if(availableProfiles.length===1)startAutomaticCombat()", wizard)
        self.assertIn("if(profileIndex<0||!Number.isInteger(profileIndex)||(!restoredRoll&&availableProfiles.length>1&&selectedValue===''))return", wizard)
        self.assertIn("$('#npoCombatProfile')?.addEventListener('change',startAutomaticCombat)", wizard)
        self.assertLess(wizard.index('id="npoCombatGuidance"'), wizard.index("${profileControl}"))

    def test_single_profiles_auto_select_for_shooting_and_melee(self):
        profiles = self.source("function npoAttackProfiles", "function canonicalAttackProfile")
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("definition.rangedWeapons||[]", profiles)
        self.assertIn("definition.meleeWeapons||[]", profiles)
        self.assertIn("availableProfiles.length===1?canonicalAttackProfile(availableProfiles[0]):null", wizard)
        self.assertIn("availableProfiles.length===1?0:Number(selectedValue)", wizard)

    def test_no_valid_profile_fails_safely_with_back_action(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        no_weapon = wizard.split("if(!availableProfiles.length){", 1)[1].split("const initialProfile", 1)[0]
        self.assertIn("No valid ${weaponType} weapon available", no_weapon)
        self.assertIn('id="cancelNpoAttack">Back</button>', no_weapon)
        self.assertNotIn("runAutomaticCombatRolls", no_weapon)

    def test_npo_guidance_is_scoped_to_attack_type_and_weapon(self):
        guidance = self.source("function normalizedGuidanceMatchText", "function recordedCombat")
        self.assertIn("function inferWeaponGuidanceContext(definition,guidanceText)", guidance)
        self.assertIn("definition?.rangedWeapons||[]", guidance)
        self.assertIn("definition?.meleeWeapons||[]", guidance)
        self.assertIn("profileId:profile.id", guidance)
        self.assertIn("item.attackType===attackType", guidance)
        self.assertIn("!profile||!item.weaponId||item.weaponId===profile.weaponId", guidance)
        self.assertIn("attackType:'shoot'", guidance)

    def test_profile_grid_is_responsive_without_empty_cells(self):
        self.assertIn(".compact-combat-profile.has-attack-profile{grid-template-columns:repeat(6,minmax(0,1fr))}", self.css)
        self.assertIn(".compact-combat-profile,.compact-combat-profile.has-attack-profile{grid-template-columns:repeat(2,minmax(0,1fr))}", self.css)
        self.assertIn(".compact-combat-profile,.compact-combat-profile.has-attack-profile{grid-template-columns:1fr}", self.css)
        self.assertIn("width:calc(100% - 16px)", self.css)


if __name__ == "__main__":
    unittest.main()
