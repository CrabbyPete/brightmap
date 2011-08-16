# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Profile'
        db.create_table('base_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('phone', self.gf('django.contrib.localflavor.us.models.PhoneNumberField')(max_length=20, null=True, blank=True)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('twitter', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('linkedin', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('is_organizer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_leadbuyer', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_attendee', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('newsletter', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('base', ['Profile'])

        # Adding model 'Organization'
        db.create_table('base_organization', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('base', ['Organization'])

        # Adding model 'Chapter'
        db.create_table('base_chapter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default=None, max_length=255)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Organization'])),
            ('organizer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('logo', self.gf('django.db.models.fields.URLField')(default=None, max_length=200, null=True)),
            ('letter', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['base.Letter'], null=True)),
            ('website', self.gf('django.db.models.fields.URLField')(default=None, max_length=200, null=True)),
        ))
        db.send_create_signal('base', ['Chapter'])

        # Adding model 'Eventbrite'
        db.create_table('base_eventbrite', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Chapter'])),
            ('user_key', self.gf('django.db.models.fields.CharField')(default=None, max_length=45)),
            ('organizer_id', self.gf('django.db.models.fields.CharField')(default=None, max_length=45)),
            ('bot_email', self.gf('django.db.models.fields.EmailField')(default=None, max_length=75, null=True)),
        ))
        db.send_create_signal('base', ['Eventbrite'])

        # Adding model 'MeetUp'
        db.create_table('base_meetup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Chapter'])),
            ('member_id', self.gf('django.db.models.fields.CharField')(default=None, max_length=45, null=True)),
            ('token', self.gf('django.db.models.fields.CharField')(default=None, max_length=45, null=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(default=None, max_length=45, null=True)),
            ('bot_email', self.gf('django.db.models.fields.EmailField')(default=None, max_length=75, null=True)),
        ))
        db.send_create_signal('base', ['MeetUp'])

        # Adding model 'LeadBuyer'
        db.create_table('base_leadbuyer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('base', ['LeadBuyer'])

        # Adding M2M table for field interests on 'LeadBuyer'
        db.create_table('base_leadbuyer_interests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('leadbuyer', models.ForeignKey(orm['base.leadbuyer'], null=False)),
            ('interest', models.ForeignKey(orm['base.interest'], null=False))
        ))
        db.create_unique('base_leadbuyer_interests', ['leadbuyer_id', 'interest_id'])

        # Adding model 'Interest'
        db.create_table('base_interest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('interest', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('base', ['Interest'])

        # Adding model 'Deal'
        db.create_table('base_deal', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('interest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Interest'])),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Chapter'])),
            ('max_sell', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('base', ['Deal'])

        # Adding model 'Term'
        db.create_table('base_term', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Deal'])),
            ('canceled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cost', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('buyer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Term'])

        # Adding model 'Expire'
        db.create_table('base_expire', (
            ('term_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.Term'], unique=True, primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('base', ['Expire'])

        # Adding model 'Cancel'
        db.create_table('base_cancel', (
            ('term_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.Term'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('base', ['Cancel'])

        # Adding model 'Count'
        db.create_table('base_count', (
            ('term_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.Term'], unique=True, primary_key=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('remaining', self.gf('django.db.models.fields.IntegerField')()),
            ('last_event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Event'], null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Count'])

        # Adding model 'Connects'
        db.create_table('base_connects', (
            ('term_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.Term'], unique=True, primary_key=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('remaining', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('base', ['Connects'])

        # Adding model 'Letter'
        db.create_table('base_letter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('letter', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('base', ['Letter'])

        # Adding model 'Event'
        db.create_table('base_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Chapter'])),
            ('event_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('describe', self.gf('django.db.models.fields.TextField')()),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('letter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Letter'], null=True, blank=True)),
        ))
        db.send_create_signal('base', ['Event'])

        # Adding model 'Survey'
        db.create_table('base_survey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Event'])),
            ('attendee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('interest', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['base.Interest'], null=True)),
            ('mailed', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('base', ['Survey'])

        # Adding model 'Connection'
        db.create_table('base_connection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('survey', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Survey'])),
            ('deal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Deal'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('base', ['Connection'])


    def backwards(self, orm):
        
        # Deleting model 'Profile'
        db.delete_table('base_profile')

        # Deleting model 'Organization'
        db.delete_table('base_organization')

        # Deleting model 'Chapter'
        db.delete_table('base_chapter')

        # Deleting model 'Eventbrite'
        db.delete_table('base_eventbrite')

        # Deleting model 'MeetUp'
        db.delete_table('base_meetup')

        # Deleting model 'LeadBuyer'
        db.delete_table('base_leadbuyer')

        # Removing M2M table for field interests on 'LeadBuyer'
        db.delete_table('base_leadbuyer_interests')

        # Deleting model 'Interest'
        db.delete_table('base_interest')

        # Deleting model 'Deal'
        db.delete_table('base_deal')

        # Deleting model 'Term'
        db.delete_table('base_term')

        # Deleting model 'Expire'
        db.delete_table('base_expire')

        # Deleting model 'Cancel'
        db.delete_table('base_cancel')

        # Deleting model 'Count'
        db.delete_table('base_count')

        # Deleting model 'Connects'
        db.delete_table('base_connects')

        # Deleting model 'Letter'
        db.delete_table('base_letter')

        # Deleting model 'Event'
        db.delete_table('base_event')

        # Deleting model 'Survey'
        db.delete_table('base_survey')

        # Deleting model 'Connection'
        db.delete_table('base_connection')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'base.cancel': {
            'Meta': {'object_name': 'Cancel', '_ormbases': ['base.Term']},
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.chapter': {
            'Meta': {'object_name': 'Chapter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['base.Letter']", 'null': 'True'}),
            'logo': ('django.db.models.fields.URLField', [], {'default': 'None', 'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Organization']"}),
            'organizer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'default': 'None', 'max_length': '200', 'null': 'True'})
        },
        'base.connection': {
            'Meta': {'object_name': 'Connection'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'deal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Deal']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Survey']"})
        },
        'base.connects': {
            'Meta': {'object_name': 'Connects', '_ormbases': ['base.Term']},
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'remaining': ('django.db.models.fields.IntegerField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.count': {
            'Meta': {'object_name': 'Count', '_ormbases': ['base.Term']},
            'last_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Event']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'remaining': ('django.db.models.fields.IntegerField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.deal': {
            'Meta': {'object_name': 'Deal'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Interest']"}),
            'max_sell': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'base.event': {
            'Meta': {'object_name': 'Event'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'describe': ('django.db.models.fields.TextField', [], {}),
            'event_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Letter']", 'null': 'True', 'blank': 'True'})
        },
        'base.eventbrite': {
            'Meta': {'object_name': 'Eventbrite'},
            'bot_email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '75', 'null': 'True'}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organizer_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45'}),
            'user_key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45'})
        },
        'base.expire': {
            'Meta': {'object_name': 'Expire', '_ormbases': ['base.Term']},
            'date': ('django.db.models.fields.DateField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.interest': {
            'Meta': {'object_name': 'Interest'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'base.leadbuyer': {
            'Meta': {'object_name': 'LeadBuyer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interests': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['base.Interest']", 'symmetrical': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'base.letter': {
            'Meta': {'object_name': 'Letter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'base.meetup': {
            'Meta': {'object_name': 'MeetUp'},
            'bot_email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '75', 'null': 'True'}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'})
        },
        'base.organization': {
            'Meta': {'object_name': 'Organization'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'base.profile': {
            'Meta': {'object_name': 'Profile'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_attendee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_leadbuyer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_organizer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'linkedin': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'base.survey': {
            'Meta': {'object_name': 'Survey'},
            'attendee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['base.Interest']", 'null': 'True'}),
            'mailed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'base.term': {
            'Meta': {'object_name': 'Term'},
            'buyer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'canceled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cost': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'deal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Deal']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['base']
