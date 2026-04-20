import json
import logging
import unidecode
import requests
from odoo import models, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("self_awb_provider", "SelfAWB")],
                                     ondelete={'self_awb_provider': 'set default'})
    self_awb_provider_package_id = fields.Many2one('stock.package.type', string="Package Info", help="Default Package")
    self_awb_service = fields.Many2one('self.awb.service', string="Self AWB Services")
    self_awb_payment = fields.Selection([('expeditor', 'Sender'), ('destinatar', 'Receiver')])
    self_awb_service_option = fields.Selection([('A', 'A - Open upon delivery'),
                                                ('B', 'B - oPOD'),
                                                ('C', 'C - Dropping off at a FAN office'),
                                                ('D', 'D - Delivery at a FAN office'),
                                                ('F', 'F - Delivery at a PayPoint store'),
                                                ('M', 'M - SMS Business'),
                                                ('O', 'O - Pick-up Prealert'),
                                                ('P', 'P - Prealert'),
                                                ('S', 'S - Open upon delivery'),
                                                ('V', 'V - PickUp'),
                                                ('W', 'W - DropOff'),
                                                ('X', 'X - ePOD'),
                                                ('Y', 'Y - mPOS')], string="Service Option", default="X")
    self_awb_deliveryMode = fields.Selection([('road', 'Road'),
                                              ('air', 'Air')], string="DeliveryMode", default="road")
    self_awb_document_type = fields.Selection([('document', 'Document'),
                                               ('non document', 'Non Document')], default="document",
                                              string="Document Type")

    def check_address_details(self, address_id, required_fields):
        """
            check the address of Shipper and Recipient
            param : address_id: res.partner, required_fields: ['zip', 'city', 'country_id', 'street']
            return: missing address message
        """

        res = [field for field in required_fields if not address_id[field]]
        if res:
            return "Missing Values For Address :\n %s" % ", ".join(res).replace("_id", "")

    def self_awb_provider_rate_shipment(self, order):
        """
           This method is used for get rate of shipment
           param : order : sale.order
           return: 'success': False : 'error message' : True
           return: 'success': True : 'error_message': False
        """
        # Shipper and Recipient Address
        shipper_address_id = order.warehouse_id.partner_id
        recipient_address_id = order.partner_shipping_id

        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['zip', 'city', 'country_id', 'street'])
        total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0

        product_weight = (order.order_line.filtered(
            lambda x: not x.is_delivery and x.product_id.type == 'product' and x.product_id.weight <= 0))
        product_name = ", ".join(product_weight.mapped('product_id').mapped('name'))

        if shipper_address_error or recipient_address_error or product_name:
            return {'success': False, 'price': 0.0,
                    'error_message': "%s %s  %s " % (
                        "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                        "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                        "product weight is not available : %s" % (product_name) if product_name else ""
                    ),
                    'warning_message': False}
        try:
            order_type = 'external-tariff' if shipper_address_id.country_id.code != recipient_address_id.country_id.code else 'internal-tariff'
            header = {
                'Authorization': 'Bearer {0}'.format(self.company_id.self_awb_authentication_token)
            }
            api_url = "{0}/reports/awb/{1}?clientId={2}&info[deliveryMode]={3}&info[documentType]={4}&info[weight]={5}&info[dimensions][height]={6}&info[dimensions][width]={7}&info[dimensions][length]={8}&info[packages][parcel]={9}&recipient[country]={10}&info[service]={11}&info[payment]={12}&recipient[locality]={13}&recipient[county]={14}".format(
                self.company_id.self_awb_api_url, order_type, self.company_id.self_awb_client_id,
                self.self_awb_deliveryMode, self.self_awb_document_type, total_weight,
                self.self_awb_provider_package_id.height,
                self.self_awb_provider_package_id.width, self.self_awb_provider_package_id.packaging_length, '1',
                shipper_address_id.country_id.code, self.self_awb_service.service_name, self.self_awb_payment,
                unidecode.unidecode(recipient_address_id.city or ''),
                unidecode.unidecode(recipient_address_id.state_id and recipient_address_id.state_id.name or ''))


            request_data = {}
            request_type = "GET"
            response_status, response_data = self.self_awb_provider_create_shipment(request_type, api_url, request_data,
                                                                                    header)
            if response_status and response_data.get('status'):
                total_charge = response_data.get('data').get('total')
                return {'success': True, 'price': total_charge,
                        'error_message': False, 'warning_message': False}
            else:
                return {'success': False, 'price': 0.0,
                        'error_message': response_data, 'warning_message': False}
        except Exception as e:
            return {'success': False, 'price': 0.0,
                    'error_message': e, 'warning_message': False}

    def self_awb_provider_retrive_single_package_info(self, height=False, width=False, length=False, weight=False,
                                                      package_name=False):
        return {
            "length": length,
            "height": height,
            "width": width
        }

    def self_awb_provider_packages(self, picking):
        #  In this method from all the parcel in pass maximum parcel dimension
        l_vls = []
        if picking.self_awb_no_of_packages:
            height = self.self_awb_provider_package_id.height
            width = self.self_awb_provider_package_id.width
            length = self.self_awb_provider_package_id.packaging_length
            total_weight = picking.shipping_weight or 1
            package_count = picking.self_awb_no_of_packages or 1
            weight = total_weight
            package = []
            for i in range(package_count):
                package.append(
                    self.self_awb_provider_retrive_single_package_info(
                        height, width, length, weight, f"{picking.name} - PKG {i + 1}"
                    )
                )
            return package
        if picking.package_ids:
            for package_id in picking.package_ids:
                height = package_id.package_type_id.height
                width = package_id.package_type_id.width
                length = package_id.package_type_id.packaging_length
                if l_vls:
                    ans_1 = l_vls[0] * l_vls[1] * l_vls[2] / 6000
                    ans_2 = height * width * length / 6000
                    if ans_2 > ans_1:
                        l_vls = [height, width, length]
                else:
                    l_vls = [height, width, length]
        if picking.weight_bulk:
            if l_vls:
                ans_1 = l_vls[0] * l_vls[1] * l_vls[2] / 6000
                ans_2 = self.self_awb_provider_package_id.height * self.self_awb_provider_package_id.width * self.self_awb_provider_package_id.packaging_length / 6000
                if ans_2 > ans_1:
                    l_vls = [self.self_awb_provider_package_id.height, self.self_awb_provider_package_id.width,
                             self.self_awb_provider_package_id.packaging_length]
            else:
                l_vls = [self.self_awb_provider_package_id.height, self.self_awb_provider_package_id.width,
                         self.self_awb_provider_package_id.packaging_length]

        height = l_vls[0]
        width = l_vls[1]
        length = l_vls[2]

        # height = self.self_awb_provider_package_id and self.self_awb_provider_package_id.height or 0
        # width = self.self_awb_provider_package_id and self.self_awb_provider_package_id.width or 0
        # length = self.self_awb_provider_package_id and self.self_awb_provider_package_id.packaging_length or 0
        weight = picking.shipping_weight
        package_name = picking.name
        package = self.self_awb_provider_retrive_single_package_info(height, width, length, weight, package_name)
        return package

    def self_awb_provider_create_shipment(self, request_type, api_url, request_data, header):
        _logger.info("Shipment Request API URL:::: %s" % api_url)
        _logger.info("Shipment Request Data:::: %s" % request_data)
        response_data = requests.request(method=request_type, url=api_url, headers=header, data=request_data)
        if response_data.status_code in [200, 201]:
            response_data = response_data.json()
            _logger.info(">>> Response Data {}".format(response_data))
            return True, response_data
        else:
            return False, response_data.text

    def self_awb_shipment_req_data(self, picking, shipper_address_id, receiver_address_id):
        packages = self.self_awb_provider_packages(picking)
        if picking.use_self_awb_custom_pack:
            parcel = picking.self_awb_no_of_packages
            envelope = 0
        else:
            parcel = len(picking.package_ids.filtered(lambda x: x.package_type_id.parcel_type == "parcel")) + (
                1 if picking.weight_bulk else 0
            )
            envelope = len(picking.package_ids.filtered(lambda x: x.package_type_id.parcel_type == "envelope"))
        # parcel = len(picking.package_ids.filtered(lambda x: x.package_type_id.parcel_type == "parcel")) + (
        #     1 if picking.weight_bulk else 0)

        cod_amount = picking.sale_id.amount_total if self.self_awb_service.service_name in ['Cont Colector',
                                                                                            'Express Loco 1H-Cont Colector',
                                                                                            'Express Loco 2H-Cont Colector',
                                                                                            'Express Loco 4H-Cont Colector',
                                                                                            "Express Loco 6H-Cont Colector",
                                                                                            'Red code-Cont Colector',
                                                                                            'Produse Albe-Cont Colector',
                                                                                            'Transport Marfa-Cont Colector',
                                                                                            'Transport Marfa Produse Albe-Cont Colector',
                                                                                            "Export-Cont Colector",
                                                                                            "CollectPoint Cont Colector",
                                                                                            "FANbox Cont Colector"] else ''
        payload = {
            "clientId": int(self.company_id.self_awb_client_id),
            "shipments": [
                {
                    "info": {
                        "service": self.self_awb_service.service_name,
                        "bank": "",
                        "bankAccount": "",
                        "packages": {
                            "parcel": parcel,
                            "envelope": envelope
                        },
                        "weight": str(picking.self_awb_custom_shipping_weight if picking.use_self_awb_custom_pack else picking.shipping_weight),
                        "cod": cod_amount,
                        "declaredValue": 0,
                        "payment": self.self_awb_payment,
                        "refund": "",
                        "returnPayment": "",
                        "observation": "",
                        "content": picking.name,
                        "dimensions": packages,
                        "costCenter": "",
                        # "options": [
                        #     self.self_awb_service_option
                        # ]
                    },
                    "recipient": {
                        "name": receiver_address_id.name or '',
                        "phone": receiver_address_id.phone or '',
                        "email": receiver_address_id.email or '',
                        "address": {
                            "county": unidecode.unidecode(receiver_address_id.state_id and receiver_address_id.state_id.name or ''),
                            "locality": unidecode.unidecode(receiver_address_id.city or ''),
                            "street": "{0} {1}".format(receiver_address_id.street or '',
                                                       receiver_address_id.street2 or ''),
                            "streetNo": "",
                            "zipCode": receiver_address_id.zip or ''
                        }
                    }
                }
            ]
        }
        if self.self_awb_service_option:
            payload.get('shipments')[0].get('info').update({"options": [self.self_awb_service_option or ' ']})
        return json.dumps(payload)

    def self_awb_provider_send_shipping(self, picking):
        shipper_address_id = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
        recipient_address_id = picking.partner_id
        company_id = self.company_id
        tracking_number = ""
        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['zip', 'city', 'country_id', 'street'])
        if shipper_address_error or recipient_address_error or not picking.shipping_weight:
            raise ValidationError("%s %s  %s " % (
                "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                "Shipping weight is missing!" if not picking.shipping_weight else ""
            ))

        # masterroot = ""
        shipping_request_data = self.self_awb_shipment_req_data(picking, shipper_address_id, recipient_address_id)
        order_type = 'extern-awb' if shipper_address_id.country_id.code != recipient_address_id.country_id.code else 'intern-awb'
        try:
            header = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {0}'.format(self.company_id.self_awb_authentication_token)
            }
            api_url = "{0}/{1}".format(self.company_id.self_awb_api_url, order_type)
            request_data = shipping_request_data
            request_type = "POST"
            response_status, response_data = self.self_awb_provider_create_shipment(request_type, api_url, request_data,
                                                                                    header)
            if response_status and response_data.get('response'):
                awb_number_ls = []
                for awb_number in response_data.get('response'):
                    if not awb_number.get('awbNumber'):
                        raise ValidationError(response_data)
                    awb_number_ls.append(str(awb_number.get('awbNumber')))
                self.generate_awb_label_using_awb_number(picking, awb_number_ls)
                shipping_data = {'exact_price': 0.0, 'tracking_number': ','.join(awb_number_ls)}
                shipping_data = [shipping_data]
                return shipping_data
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def generate_awb_label_using_awb_number(self, picking, awb_number_ls):
        for awb_number in awb_number_ls:
            url = "{0}/awb/label?language=en&clientId={1}&awbs[]={2}&pdf=1".format(self.company_id.self_awb_api_url,
                                                                                   self.company_id.self_awb_client_id,
                                                                                   awb_number)
            payload = {}
            headers = {
                'Authorization': 'Bearer {0}'.format(self.company_id.self_awb_authentication_token)
            }
            response_data = requests.request("GET", url, headers=headers, data=payload)
            _logger.info("Label Printing Response : %s" % response_data)
            if response_data.status_code in [200, 201]:
                picking.message_post(body="Label created sucessfully!<br/>", attachments=[
                    ('%s.%s' % (picking.name, "pdf"), response_data.content)])
            else:
                return response_data.text

    def self_awb_provider_cancel_shipment(self, picking):
        url = "{0}/awb?clientId={1}&awb={2}".format(self.company_id.self_awb_api_url,
                                                    self.company_id.self_awb_client_id, picking.carrier_tracking_ref)

        payload = {}
        headers = {
            'Authorization': 'Bearer {0}'.format(self.company_id.self_awb_authentication_token)
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)
        _logger.info("Cancel Response %s" % response)
        if response.status_code in [200, 201]:
            cancel_response = response.json()
            if cancel_response.get('status') == 'success':
                _logger.info("Successfull deleted order")
                return True
            else:
                raise ValidationError(cancel_response)
        else:
            raise ValidationError(response.text)

    def self_awb_provider_get_tracking_link(self, picking):
        return "https://www.fancourier.ro/en/awb-tracking?awb={0}".format(picking.carrier_tracking_ref)
