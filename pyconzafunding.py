

from __future__ import print_function, unicode_literals, absolute_import, division

import functools

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, UnicodeText, Boolean, Numeric

from reahl.web.fw import UserInterface, Widget, CannotCreate, UrlBoundView, Detour, ViewPreCondition, Url

from reahl.domain.systemaccountmodel import AccountManagementInterface, EmailAndPasswordSystemAccount, NoSuchAccountException

from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, TextNode, Div, H, P, A
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.tables import Table, TableLayout
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.bootstrap.forms import TextInput, TextArea, Form, FormLayout, Button, ButtonLayout, FieldSet, CheckboxInput
from reahl.component.modelinterface import exposed, Field, EmailField, Action, Event, IntegerField, BooleanField

from reahl.sqlalchemysupport import Session, Base, ForeignKey

from reahl.domain.systemaccountmodel import LoginSession
from reahl.domainui.bootstrap.accounts import AccountUI


african_countries = [
    'Angola',
    'Benin', 
    'Botswana', 
    'Burkina Faso', 
    'Burundi', 
    'Cameroon',
    'The Republic of Cabo Verde', 
    'The Central African Republic',
    'Chad', 
    'Comoros', 
    'Democratic Republic of Congo',
    'Republic of Congo', 
    'Cote d’Ivoire', 
    'Djibouti', 
    'Egypt', 
    'Equatorial Guinea',
    'Eritrea',
    'Ethiopia', 
    'Gabon',
    'Gambia', 
    'Ghana', 
    'Guinea',
    'Guinea-Bissau',
    'Kenya', 
    'Lesotho', 
    'Liberia', 
    'Libya', 
    'Madagascar',
    'Malawi', 
    'Mali', 
    'Mauritania', 
    'Mauritius', 
    'Morocco', 
    'Mozambique',
    'Namibia', 
    'Niger', 
    'Nigeria', 
    'Rwanda',
    'Republic Arab Saharawi Democratic',
    'São Tomé and Príncipe',
    'Senegal', 
    'Seychelles', 
    'Sierra Leone',
    'Somalia', 
    'South Africa',
    'South Sudan',
    'Sudan',
    'Swaziland', 
    'Swaziland', 
    'Tanzania', 
    'Togo',
    'Tunisia',
    'Uganda', 
    'Zambia', 
    'Zimbabwe'
        ]

class LogoutForm(Form):
    def __init__(self, view):
        super(LogoutForm, self).__init__(view, 'logout')
        accounts = AccountManagementInterface.for_current_session()
        self.define_event_handler(accounts.events.log_out_event)
        self.add_child(Button(self, accounts.events.log_out_event))

        
class FundingRequestPage(HTML5Page):
    def __init__(self, view, bookmarks):
        super(FundingRequestPage, self).__init__(view)

        self.head.add_css(Url('/css/pyconza2019.css'))

        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize())).with_slots()
        self.layout.contents.use_layout(contents_layout)

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text('PyConZA 2019 Financial Aid')
        navbar.layout.add(Nav(view).with_bookmarks(bookmarks))

        if LoginSession.for_current_session().is_logged_in():
            navbar.layout.add(LogoutForm(view))

        self.layout.header.add_child(navbar)


class EditView(UrlBoundView):
    def assemble(self, funding_request_id=None):
        try:
            #TODO: only filter/guard for logged in user/super user
            funding_request = Session.query(FundingRequest).filter_by(id=funding_request_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = 'Edit Financial Aid Application for %s' % funding_request.name
        self.set_slot('main', EditFundingRequestForm.factory(funding_request))


class MyCheckboxInput(CheckboxInput):

    def get_value_from_input(self, input_values):
        if self.bound_field.allows_multiple_selections:
            return input_values.getall(self.name)
        else:
            return input_values.get(self.name, self.bound_field.false_value) #TODO: this fixes a bug - see test_marshalling_of_checkbox_select_input, and add a similar test using a BooleanField


class FundingRequestForm(Form):
    def __init__(self, view, unique_id, funding_request, submit_event):
        super(FundingRequestForm, self).__init__(view, unique_id)

        personal_info = self.add_child(FieldSet(view, legend_text='Personal information'))
        personal_info.use_layout(FormLayout())
        personal_info.layout.add_input(TextInput(self, funding_request.fields.name))
        personal_info.layout.add_input(TextInput(self, funding_request.fields.surname))
        personal_info.layout.add_input(TextInput(self, funding_request.fields.email_address))
        personal_info.layout.add_input(TextInput(self, funding_request.fields.username_on_za))

        personal_info.layout.add_input(TextInput(self, funding_request.fields.origin_country))
        personal_info.layout.add_input(TextInput(self, funding_request.fields.resident_country))

        application = self.add_child(FieldSet(view, legend_text='Application'))
        application.use_layout(FormLayout())
        application.layout.add_input(TextInput(self, funding_request.fields.amount_requested))
        application.layout.add_input(TextInput(self, funding_request.fields.budget_own_contribution))
        application.layout.add_input(TextArea(self, funding_request.fields.motivation))
        application.layout.add_input(MyCheckboxInput(self, funding_request.fields.willing_to_help))

        budget = self.add_child(FieldSet(view, legend_text='Budget'))
        budget.use_layout(FormLayout())
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_ticket))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_travel))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_accommodation))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_food))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_transport))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_other))
        budget.layout.add_input(TextInput(self, funding_request.fields.budget_other_describe))


        admin_inputs = self.add_child(FieldSet(view, legend_text='Admin'))
        admin_inputs.use_layout(FormLayout())
        admin_inputs.layout.add_input(MyCheckboxInput(self, funding_request.fields.allow_user_changes))
        admin_inputs.layout.add_input(TextInput(self, funding_request.fields.grant_status))
        admin_inputs.layout.add_input(TextArea(self, funding_request.fields.feedback_message))
        admin_inputs.layout.add_input(TextInput(self, funding_request.fields.number_talks_proposed))
        admin_inputs.layout.add_input(TextInput(self, funding_request.fields.number_talks_accepted))
        admin_inputs.layout.add_input(TextInput(self, funding_request.fields.number_keynote_talks))

        
        button = self.add_child(Button(self, submit_event))
        button.use_layout(ButtonLayout(style='primary'))

        
class EditFundingRequestForm(FundingRequestForm):
    def __init__(self, view, funding_request):
        super(EditFundingRequestForm, self).__init__(view, 'edit_form', funding_request, funding_request.events.update)
        
class NewFundingRequestForm(FundingRequestForm):
    def __init__(self, view, new_request=None):
        request = new_request or FundingRequest()
        super(NewFundingRequestForm, self).__init__(view, 'new_application_form', request, request.events.save)



class AllFundRequestsPanel(Widget):
    def __init__(self, view):
        super(AllFundRequestsPanel, self).__init__(view)

        funding_requests = FundingRequest.find_requests()

        def make_edit_link(view, funding_request):
            form = Form(view, 'edit_%s' % funding_request.id)
            form.add_child(Button(form, funding_request.events.edit.with_arguments(funding_request_id=funding_request.id)))
            return form

        columns = [StaticColumn(field.unbound_copy(), field.name) for field in FundingRequest().fields.values()]
        columns.append(DynamicColumn('', make_edit_link))

        table = self.add_child(Table(view, caption_text='Financial Aid Applications'))
        table.use_layout(TableLayout(responsive=True,striped=True))
        table.with_data(columns, funding_requests)

        
class ScoringDataPanel(Widget):
    def __init__(self, view):
        super(ScoringDataPanel, self).__init__(view)

        class Row(object):
            def __init__(self, request):
                self.request = request
                self.criteria = {i.label:i for i in self.request.get_criteria()}

            def does_criterion_apply(self, criterion):
                return self.criteria[criterion.label].applies
            def value_for(self, criterion):
                return self.criteria[criterion.label].score

            @property
            def score_total(self):
                return self.request.score_total
            @property
            def name(self):
                return self.request.name
            @property
            def surname(self):
                return self.request.surname
            

        def make_column_value(criterion, view, row):
            return TextNode(view, ('yes' if row.does_criterion_apply(criterion) else 'no'))

        def make_score_column_value(criterion, view, row):
            return TextNode(view, str(row.value_for(criterion)))

        columns = []
        columns.append(StaticColumn(IntegerField(label='Name'), 'name'))
        columns.append(StaticColumn(IntegerField(label='Surname'), 'surname'))
        for i in FundingRequest().get_criteria():
            columns.append(DynamicColumn(i.label, functools.partial(make_column_value, i)))
            columns.append(DynamicColumn('#', functools.partial(make_score_column_value, i)))
        columns.append(StaticColumn(IntegerField(label='Total'), 'score_total'))
            
        rows = [Row(i) for i in FundingRequest.find_requests()]
        table = self.add_child(Table(view, caption_text='Financial Aid Applications'))
        table.use_layout(TableLayout(responsive=True,striped=True))
        table.with_data(columns, rows)


class QualifyDataPanel(Widget):
    def __init__(self, view):
        super(QualifyDataPanel, self).__init__(view)

        class QualifyDataRow(object):
            def __init__(self, request):
                self.request = request
                self.funding_items = {i.label:i for i in self.request.get_funding_items()}

            def qualifies_for_amount(self, funding_item):
                return self.funding_items[funding_item.label].qualified_amount

            @property
            def score_total(self):
                return self.request.score_total
            @property
            def qualify_total(self):
                return self.request.qualify_total
            @property
            def name(self):
                return self.request.name
            @property
            def surname(self):
                return self.request.surname
            

        def make_column_value(funding_item, view, row):
            return TextNode(view, str(row.qualifies_for_amount(funding_item)))

        columns = []
        columns.append(StaticColumn(IntegerField(label='Name'), 'name'))
        columns.append(StaticColumn(IntegerField(label='Surname'), 'surname'))
        columns.append(StaticColumn(IntegerField(label='Score'), 'score_total'))
        for i in FundingRequest().get_funding_items():
            columns.append(DynamicColumn(i.label, functools.partial(make_column_value, i)))

        columns.append(StaticColumn(IntegerField(label='Total'), 'qualify_total'))
            
        rows = [QualifyDataRow(i) for i in FundingRequest.find_requests()]
        table = self.add_child(Table(view, caption_text='Qualifying amounts'))
        table.use_layout(TableLayout(responsive=True, striped=True))
        table.with_data(columns, rows)

        
class FundingRequestBox(Form):
    def __init__(self, view, funding_request):
        form_name = 'fund_%s' % funding_request.id  # Forms need unique names!
        super(FundingRequestBox, self).__init__(view, form_name)
        allow_edit_symbol = '…' if funding_request.allow_user_changes else '⏹'
        paragraph = self.add_child(P(view, text='%s : %s: %s' % (allow_edit_symbol, funding_request.name, funding_request.email_address)))
        paragraph.add_child(Button(self, funding_request.events.edit.with_arguments(funding_request_id=funding_request.id)))


class MyFundingRequest(Widget):
    def __init__(self, view):
        super(MyFundingRequest, self).__init__(view)

        if not CurrentUserSession().is_logged_in_as_super_user():
            funding_requests = FundingRequest.find_requests(account=CurrentUserSession().account)
            if len(funding_requests) == 1:
                funding_request = funding_requests[0]
                self.add_child(EditFundingRequestForm(view, funding_request))
            else:
                funding_request = FundingRequest()
                self.add_child(NewFundingRequestForm(view, funding_request))


class FundingRequestSummary(Widget):
    def __init__(self, view, funding_request, apply_bookmark):
        super(FundingRequestSummary, self).__init__(view)

        self.add_child(H(view, 1, 'Application for Financial Aid'))
        self.add_child(P(view, text='Name: %s' % funding_request.name))
        self.add_child(P(view, text='Surname: %s' % funding_request.surname))
        self.add_child(P(view, text='Email: %s' % funding_request.email_address))
        self.add_child(P(view, text='Current status: %s.' % funding_request.grant_status))

        self.add_child(H(view, 2, 'Feedback from the financial aid team'))
        if funding_request.feedback_message:
            self.add_child(P(view, text=funding_request.feedback_message))
        else:
            self.add_child(P(view, text='There is no feedback message for you from the organisers'))
            
        if funding_request.allow_user_changes:
            self.add_child(P(view, text='You can still edit/change your request'))
            self.add_child(Nav(view).with_bookmarks([apply_bookmark.with_description('Edit application')]))

            



        
        
class MyFundingRequestStatus(Widget):
    def __init__(self, view, apply_bookmark):
        super(MyFundingRequestStatus, self).__init__(view)
    
        if not CurrentUserSession().is_logged_in_as_super_user():
            funding_requests = FundingRequest.find_requests(account=CurrentUserSession().account)
            if len(funding_requests) == 1:
                funding_request = funding_requests[0]
                self.add_child(FundingRequestSummary(view, funding_request, apply_bookmark))
            else:
                self.add_child(P(view, text='You have not applied for financial aid yet.'))
                self.add_child(Nav(view).with_bookmarks([apply_bookmark.with_description('Apply here!')]))
                self.add_child(P(view, text='Once you have applied, please check back here to see the status of your application.'))



                
class LoginFirst(Div):
    def __init__(self, view, accounts):
        super(LoginFirst, self).__init__(view)
        self.use_layout(Container())

        self.accounts = accounts

        self.add_child(P(view, text='You are not logged in. Please log into your account to apply for, or check the status of your financial aid.'))
        self.add_child(Nav(view).with_bookmarks([accounts.get_bookmark(relative_path='/login'), accounts.get_bookmark(relative_path='/register')]))


class CurrentUserSession(object):
    super_user_email_address = 'admin@example.org'

    def __init__(self):
        self.login_session = LoginSession.for_current_session()

    @property
    def account(self):
        return self.login_session.account

    def is_logged_in(self):
        return self.account

    def is_logged_in_as_normal_user(self):
        return self.is_logged_in() and not self.is_logged_in_as_super_user()

    def is_logged_in_as_super_user(self):
        return self.is_logged_in() and self.get_logged_in_user_email() == self.super_user_email_address

    def get_logged_in_user_email(self):
        if self.is_logged_in():
            return self.account.email
        return None

    def setup_super_and_example_account(self):
        example_accounts = ['applicant%s@example.org' % i for i in range(100)]
        for email in [self.super_user_email_address]+example_accounts:
            try:
                EmailAndPasswordSystemAccount.by_email(email)
            except NoSuchAccountException:
                system_account = EmailAndPasswordSystemAccount(email=email)
                system_account.set_new_password(email, 'snakesnake')
                system_account.activate()
                Session.add(system_account)


                
class FundingRequestUI(UserInterface):
    created = False
    def assemble(self):

        self.define_static_directory('/css')

        user_session = CurrentUserSession()

        if not self.created:
            user_session.setup_super_and_example_account()
            self.created = True

        home = self.define_view('/', title='PyConZA 2019 Financial Aid')

        accounts = self.define_accounts()

        myapplication = self.define_view('/myapplication', title='My Application for Financial Aid', read_check=user_session.is_logged_in_as_normal_user)
        myapplication.set_slot('main', MyFundingRequest.factory())

        if user_session.is_logged_in():
            home.set_slot('main', MyFundingRequestStatus.factory(myapplication.as_bookmark(self)))
        else:
            home.set_slot('main', LoginFirst.factory(accounts))
        
        requests = self.define_view('/requests', title='Funding Requests', read_check=user_session.is_logged_in_as_super_user)
        requests.set_slot('main', AllFundRequestsPanel.factory())

        scores = self.define_view('/scores', title='Scoring data', read_check=user_session.is_logged_in_as_super_user)
        scores.set_slot('main', ScoringDataPanel.factory())

        results = self.define_view('/results', title='Funding', read_check=user_session.is_logged_in_as_super_user)
        results.set_slot('main', QualifyDataPanel.factory())

        create = self.define_view('/create', title='Create', read_check=user_session.is_logged_in_as_super_user)
        create.set_slot('main', NewFundingRequestForm.factory())

        self.edit = self.define_view('/edit', view_class=EditView, funding_request_id=IntegerField(), read_check=user_session.is_logged_in)


        account_bookmarks = []
        if not user_session.is_logged_in():
            account_bookmarks = [accounts.get_bookmark(relative_path=relative_path)
                                 for relative_path in ['/login', '/register', '/registerHelp', '/verify']]
        funding_bookmarks = [f.as_bookmark(self) for f in [create, requests, scores, results]]
        self.define_page(FundingRequestPage, funding_bookmarks+account_bookmarks)

        self.define_transition(FundingRequest.events.save, create, requests)
        self.define_transition(FundingRequest.events.update, self.edit, requests)
        self.define_transition(FundingRequest.events.edit, requests, self.edit)
        self.define_transition(FundingRequest.events.save, myapplication, home)
        self.define_transition(FundingRequest.events.update, myapplication, home)


    def define_accounts(self):

        terms_of_service = self.define_view('/terms_of_service', title='Terms of service')
        terms_of_service.set_slot('main', LegalNotice.factory('The terms of services defined as ...', 'terms'))

        privacy_policy = self.define_view('/privacy_policy', title='Privacy policy')
        privacy_policy.set_slot('main', LegalNotice.factory('You have the right to remain silent ...', 'privacypolicy'))

        disclaimer = self.define_view('/disclaimer', title='Disclaimer')
        disclaimer.set_slot('main', LegalNotice.factory('Disclaim ourselves from negligence ...', 'disclaimer'))

        class LegalBookmarks(object):
            terms_bookmark = terms_of_service.as_bookmark(self)
            privacy_bookmark = privacy_policy.as_bookmark(self)
            disclaimer_bookmark = disclaimer.as_bookmark(self)

        return self.define_user_interface('/accounts', AccountUI,
                                          {'main_slot': 'main'},
                                          name='legal', bookmarks=LegalBookmarks)


class LegalNotice(P):
    def __init__(self, view, text, name):
        super(LegalNotice, self).__init__(view, text=text, css_id=name)
        self.set_as_security_sensitive()




        
class Criterion(object):
    def __init__(self, label, score_contribution, applies):
        self.label = label
        self.score_contribution = score_contribution
        self.applies = applies

    @property
    def score(self):
        return self.score_contribution if self.applies else 0

    
class FundingItem(object):
    def __init__(self, label, score_needed, value, total_score):
        self.label = label
        self.score_needed = score_needed
        self.value = value
        self.total_score = total_score

    @property
    def qualified_amount(self):
        if self.total_score >= self.score_needed:
            return self.value
        else:
            return 0
        

class FundingRequest(Base):
    __tablename__ = 'pyconza_funding_request'

    id              = Column(Integer, primary_key=True)

    account_id    = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    account       = relationship(EmailAndPasswordSystemAccount)
    
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    surname       = Column(UnicodeText)
    username_on_za   = Column(UnicodeText)
    origin_country   = Column(UnicodeText)
    resident_country = Column(UnicodeText)
    motivation       = Column(UnicodeText)
    willing_to_help = Column(Boolean, nullable=False, default=False)
    amount_requested = Column(Integer, default=0)
    budget_own_contribution = Column(Integer, default=0)
    budget_ticket    = Column(Integer, default=0)
    budget_travel    = Column(Integer, default=0)
    budget_accommodation = Column(Integer, default=0)
    budget_food      = Column(Integer, default=0)
    budget_transport = Column(Integer, default=0)
    budget_other     = Column(Integer, default=0)
    budget_other_describe = Column(UnicodeText, default='')
    
    allow_user_changes = Column(Boolean, nullable=False, default=True)
    grant_status  = Column(UnicodeText, default='Pending')
    feedback_message = Column(UnicodeText, default='')

    number_talks_proposed = Column(Integer, default=0)
    number_talks_accepted = Column(Integer, default=0)
    number_keynote_talks = Column(Integer, default=0)

    def __init__(self):
        super(FundingRequest, self).__init__()
        self.name          = ''
        self.surname       = ''

        user_session = CurrentUserSession()
        if user_session.is_logged_in_as_normal_user():
            self.email_address = user_session.get_logged_in_user_email()

        self.username_on_za   = ''
        self.origin_country   = ''
        self.resident_country = ''
        self.motivation       = ''
        self.willing_to_help = False
        self.amount_requested = 0
        self.budget_own_contribution = 0
        self.budget_ticket    = 0
        self.budget_travel    = 0
        self.budget_accommodation = 0
        self.budget_food      = 0
        self.budget_transport = 0
        self.budget_other     = 0
        self.budget_other_describe = ''

        self.allow_user_changes = True
        self.grant_status  = 'Pending'
        self.feedback_message = ''

        self.number_talks_proposed = 0
        self.number_talks_accepted = 0
        self.number_keynote_talks = 0

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True, writable=Action(self.user_may_edit))
        fields.email_address = EmailField(label='Email', required=self.is_user_super_user(), writable=Action(self.is_user_super_user))

        fields.surname = Field(label='Surname', required=True, writable=Action(self.user_may_edit))
        fields.username_on_za = Field(label='Username on za.pycon.org', required=True, writable=Action(self.user_may_edit))
        fields.origin_country = Field(label='Country of origin', required=True, writable=Action(self.user_may_edit))
        fields.resident_country = Field(label='Country of residence', required=True, writable=Action(self.user_may_edit))
        fields.motivation = Field(label='Motivation', required=True, writable=Action(self.user_may_edit))

        fields.willing_to_help = BooleanField(label='Are you willing to help out at the event?', writable=Action(self.user_may_edit))
        
        fields.total_expenses   = IntegerField(label='Total expenses', required=True, writable=Action(self.user_may_edit))
        fields.amount_requested = IntegerField(label='Aid amount requested', required=True, writable=Action(self.user_may_edit))
        fields.budget_own_contribution = IntegerField(label='Own contribution', required=True, writable=Action(self.user_may_edit))
        fields.budget_ticket = IntegerField(label='Conference ticket', writable=Action(self.user_may_edit))
        fields.budget_travel = IntegerField(label='Travel',  writable=Action(self.user_may_edit))
        fields.budget_accommodation = IntegerField(label='Accommodation',  writable=Action(self.user_may_edit))
        fields.budget_food = IntegerField(label='Food', writable=Action(self.user_may_edit))
        fields.budget_transport = IntegerField(label='Local transport', writable=Action(self.user_may_edit))
        fields.budget_other = IntegerField(label='Other expenses', writable=Action(self.user_may_edit))
        fields.budget_other_describe = Field(label='Explaination of other expenses', writable=Action(self.user_may_edit))
        
        fields.allow_user_changes = BooleanField(label='Allow user changes', default=True,
                                                   readable=Action(self.is_user_super_user),
                                                   writable=Action(self.is_user_super_user))

        fields.number_talks_proposed = IntegerField(label='Number of talks proposed',
                                                    readable=Action(self.is_user_super_user),
                                                    writable=Action(self.is_user_super_user))
        fields.number_talks_accepted = IntegerField(label='Number of talks accepted',
                                                    readable=Action(self.is_user_super_user),
                                                    writable=Action(self.is_user_super_user))
        fields.number_keynote_talks = IntegerField(label='Number of talks accepted as keynote',
                                                   readable=Action(self.is_user_super_user),
                                                   writable=Action(self.is_user_super_user))

        fields.grant_status = Field(label='Application status', writable=Action(self.is_user_super_user))
        fields.feedback_message = Field(label='Feedback', writable=Action(self.is_user_super_user))

    def get_criteria(self):
        return [Criterion('Accepted speaker?', 35, self.number_talks_accepted > 0),
                Criterion('Additional talks accepted?', 10, self.number_talks_accepted > 1),
                Criterion('Accepted for keynote?', 20, self.number_keynote_talks > 0),
                Criterion('Will provide lightning talk?', 10, False),
                Criterion('Lives in Africa?', 25, self.lives_in_africa),
                Criterion('Lives in SA', 10, self.lives_in_sa),
                Criterion('Willing to help at venue?', 10, self.willing_to_help)
        ]

    def get_funding_items(self):
        return [FundingItem('Conference ticket', 10, self.budget_ticket, self.score_total),
                FundingItem('Travel', 60, self.budget_travel, self.score_total),
                FundingItem('Accommodation', 60, self.budget_accommodation, self.score_total),
                FundingItem('Food', 30, self.budget_food, self.score_total),
                FundingItem('Local transport', 30, self.budget_transport, self.score_total)
        ]
    
    @property
    def lives_in_africa(self):
        return self.resident_country in african_countries
    
    @property
    def lives_in_sa(self):
        return self.resident_country == 'South Africa'

    @property
    def score_total(self):
        return sum([criterion.score for criterion in self.get_criteria()])

    @property
    def qualify_total(self):
        return sum([item.qualified_amount for item in self.get_funding_items()])

    def save(self):
        login_session = LoginSession.for_current_session()
        self.account = login_session.account
        Session.add(self)

    @exposed('save', 'update', 'edit')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))
        events.update = Event(label='Update')
        events.edit = Event(label='Edit')#writable=Action(lambda: self.is_user_super_user() or self.allow_user_changes)

    def user_may_edit(self):
        user_session = CurrentUserSession()
        return user_session.is_logged_in_as_super_user() or (user_session.is_logged_in() and self.allow_user_changes)

    def is_user_super_user(self):
        user_session = CurrentUserSession()
        if user_session.is_logged_in_as_super_user():
            return True
        else:
            return False

    @classmethod
    def find_requests(cls, account=None):
        if not account:
            return Session.query(FundingRequest).all()
        else:
            return Session.query(FundingRequest).filter_by(account=account).all()
