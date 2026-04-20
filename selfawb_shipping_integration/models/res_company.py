from odoo import models, fields
from odoo.exceptions import ValidationError
from requests import request
import logging

_logger = logging.getLogger("SelfAWB")



class ResCompany(models.Model):
    _inherit = 'res.company'

    use_self_awb_shipping_provider = fields.Boolean(copy=False, string="Are You Use SelfAWB Shipping Provider.?",
                                                help="If use SelfAWB shipping provider than value set TRUE.",
                                                default=False)
    self_awb_api_url = fields.Char(string="API URL",default="https://api.fancourier.ro", copy=False)
    self_awb_username = fields.Char(string="Username",help="Username will get from self awb team")
    self_awb_password = fields.Char(string="Password",help="Password will get from self awb team")
    self_awb_client_id = fields.Char(string="ClientId",help="ClientId will get from self awb team")
    self_awb_authentication_token = fields.Char(string="Authentication Token",help="Based on your credentials we need to generate authorisation token")

    def generate_self_awb_authorisation_token(self):

        api_url = "{0}/login?username={1}&password={2}".format(
            self.self_awb_api_url, self.self_awb_username, self.self_awb_password)
        _logger.info("SelfAWB API URL:::: %s" % api_url)
        try:
            response = request("POST", api_url)
            if response.status_code in [200, 201]:
                response_data = response.json()
                _logger.info("Authorization Token :::: %s" % response_data)
                if response_data.get('status') == 'success':
                    self.self_awb_authentication_token = response_data.get('data').get('token')
                    return {
                        'effect': {
                            'fadeout': 'slow',
                            'message': "Yeah! SelfAWB Token Retrieved successfully!!",
                            'img_url': '/web/static/img/smile.svg',
                            'type': 'rainbow_man',
                        }
                    }
                else:
                    raise ValidationError(response_data)
            else:
                raise ValidationError(response.text)
        except Exception as e:
            raise ValidationError(e)

    def generate_self_awb_refresh_token_using_cron(self, ):
        for credential_id in self.search([]):
            try:
                if credential_id.self_awb_authentication_token:
                    credential_id.generate_self_awb_authorisation_token()
            except Exception as e:
                _logger.info("Getting an error in Generate Token request Odoo to SelfAWB: {0}".format(e))

    def import_self_awb_service(self):
        api_url = "{0}/reports/services".format(self.self_awb_api_url)
        available_service_obj = self.env['self.awb.service']
        try:
            headers = {
                'Authorization': 'Bearer {0}'.format(self.self_awb_authentication_token)
            }
            response_data = request('GET',url=api_url,headers=headers)
            if response_data.status_code in [200, 201]:
                response_data = response_data.json()
                for service in response_data.get('data'):
                    service_name = service.get('name')
                    service_description = service.get('description')
                    if not available_service_obj.sudo().search([('service_name', '=', '{}'.format(service_name))]):
                        available_service_obj.sudo().create({'service_name': '{}'.format(service_name),
                                                             'service_description': '{}'.format(service_description)})
                    else:
                        _logger.info("carrier is already exist")
                        available_service_obj.sudo().write({'service_name': '{}'.format(service_name),
                                                            'service_description': '{}'.format(service_description)})
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! Service Successfully Import.",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }

            else:
                raise ValidationError("Get Some Error In Response {}".format(response_data.text))
        except Exception as E:
            raise ValidationError(E)



