from django.test import TestCase
from .forms import TrainerForm
from .models import Trainer

class TrainerFormActivityTest(TestCase):
    def test_trainer_is_active_by_default(self):
        # Data without is_active
        data = {
            'name': 'Active Trainer',
            'country_code': '+91',
            'phone_number': '1234567890',
            'email': 'active@trainer.com',
            'employment_type': 'FT',
            'years_of_experience': 5,
            'timing_slots': '[]',
            'commercials': '[]'
        }
        form = TrainerForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        trainer = form.save()
        
        # Check if the saved trainer is active (should use model default)
        self.assertTrue(trainer.is_active)
