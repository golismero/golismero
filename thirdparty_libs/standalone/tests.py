# -*- coding: utf8 -*-

from django.test import TestCase

"""
Testcases for django-standalone. Run with the provided test.py script.
"""

class DjangoStandaloneTests(TestCase):

    def setUp(self):
        # build some test models we need for test cases
        from django.core.management import call_command
        from standalone import models
        
        class MyModel(models.StandaloneModel):

            force_install_standalone_models = True

            col1 = models.CharField(max_length=1000)
            col2 = models.IntegerField()
            col3 = models.BooleanField()

            def __unicode__(self):
                return self.col1

        class MyOtherModel(models.StandaloneModel):

            col1 = models.CharField(max_length=100)
            col2 = models.ForeignKey("standalone.MyModel")

        call_command('syncdb')

    def test_environment(self):
        """
        Just make sure that all is set up correctly.
        """
        self.assert_(True)

    def test_namespaces(self):
        """
        test that models are in the right namespaces
        (or are not in the right namespaces)
        """
        import standalone.models
        self.assert_(hasattr(standalone.models, 'MyModel'))
        self.assert_(not(hasattr(standalone.models, 'MyOtherModel')))

    def test_create_objects(self):
        """
        Create a few objects in the database and check
        that they are actually where they belong.
        """
        from models import MyModel
        o1 = MyModel(col1='foo', col2=1, col3=True)
        o1.save()
        o2 = MyModel(col1='bar', col2=2, col3=False)
        o2.save()
        self.assertEquals(MyModel.objects.get(col2=1).col1, 'foo')
        self.assertEquals(MyModel.objects.get(col2=2).col1, 'bar')

