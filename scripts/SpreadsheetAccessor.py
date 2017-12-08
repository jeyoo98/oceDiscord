import json
import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from scripts import Zone
from gspread import utils
from json.decoder import JSONDecodeError


class SpreadsheetAccessor:
    def __init__(self, logger):
        # Variable instantiations
        self.timezone = Zone.Zone(10, True, 'AEST')
        self.client = None
        self.credentials = None
        self.scope = ['https://spreadsheets.google.com/feeds/']
        self.SpreadsheetObjects = {}

        self.data = {"type":                          os.environ['gapi_type'],
                     "project_id":                    os.environ['gapi_project_id'],
                     "private_key_id":                os.environ['gapi_private_key_id'],
                     "private_key":                   "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCspEjnu7JsF1D6\nXmXvNt4D+Z3gLpEvWxrKoJbwIlDYTMFeSsXdknrugz5/MOEfhNu01NGwE8B9RhhA\nc7vmlxlC6fXtmBnKm90Xxyvy5DWwzWbqNS4u4StMlkqLupA84UxgpXShLo20pBAX\nrPt5bpTrNYLCv/R0J+c6nEm3b/n81siUEHYMZSsw4sBivR3JSC0iIAxv0MUDzRNj\nSMDGhbtMjq1iOSHj/TJUCgxDB2tRFSUIgK9ACDdnQmscVsKj7CwT2fWVs4K2gvxa\nvwrsJfFX4lGgRW3qV5LK+zv+J9nDqM4gK4f5ErANRSE3PY2f+7wkGKVmxCPHRA9m\nNgmt+CzFAgMBAAECggEBAIK3qZP8pG3/gYrw6tGjg5sS550U5U0r+C8wRNjxwrDj\n/Q2+I+9Ot9HcgfegNPS+jfRvp41gh0DTUA2NE9rW0YO+zjzmC7FDLraQUhCJBrYl\n8CSpu5w3VaeZrDv8OLZACKqs3JAmRZlfF+g1S/t35T3quGVpHljM1eGk8JP6Lxhm\n8Oi6boDVdMNPCtLis15nRRG1RKui1SEBKxPyaZD25MCzmI2crzPOVJ1idb/wKTH4\nrNsN5jrjAE+IZ98viqIR/XKAXAzqxxY2H8dr4Ra6Cb7dzqKvp/EbnvTmzDtOQsE8\nhoxUEbdaCyDQOG59IxPg7gukKHkYszsMrcXWooION8kCgYEA5GIJOpC/WGZSTZT3\n9+yG1V0U/73Mb/Qdnbs26X3n8fCcWxGFZtTR1qfQOGwU12uREWZnGQLeFkDBPBpm\nDdR3UpYNQVFHZGsMZpKZr872v4XcVCNmM8Ueb4Nu3vnBsghFTP8mj8nj+vYS2/B2\nukigeBzQVPvdtvcid5cEed5PPiMCgYEAwYSwblLXGrGIpbk4FtLDnZOGe183rlgD\nWDQD8fLXJVNcNXBxtj+gCCutu+5G6+szqgpG5Zx8e0vKSi1PUsVM4U9Wsb47f/hg\nXDMKzhg/HOQNH1v3Y377VSdt+zZYkOqTnk3L3pFUG5CKGfKQNu+JZd5Zk1gQTdw8\nFdya2u7Y8/cCgYACQhXlRlkd/qUBr19kTCppIap7fNzwnnFMhfVdCampcr+ZButS\nwPfyL2aXqDnsh1u/2Etcq/KWNb2zYm9v45HqdyFaa/tQut48hWaPnnRCIIi1LERu\nbpyGbb5C5iVMJVjKEhvHgC+I47X8BrylyuILTf2hWXwvuvHUTOH2coRGEQKBgFxa\nIojD5/vJNdlA50+dDdWpjchazIvbXN0/FZLlvV8GxT6LhvjerFS545OIRzhXarR/\naw4w/AcrSELWFMD/f40W+9yfWG3d7r6RbVqln5j+DHUmwo0tEGy3AHmeme2uxPwL\nTHvPB0CQXhe79q8A6aU/06fJox5FODeGrDBHRCpJAoGALp3ksA+utXA7vPTkVzak\nbpovkoeZeYloXU00YluODTY+IQnyrgxSkj27oUbjIF4e7lwFbegZhVTQ+p0GsvDF\nDtM70C1ylkJkSoKqoo0NCfSiOJXF6/WwbxINH3UTWeRv4n9H7bDCHgT1mwid303/\nW8WfWBwrEtp9qVvS1V6CzQI=\n-----END PRIVATE KEY-----\n",
                     "client_email":                  os.environ['gapi_client_email'],
                     "client_id":                     os.environ['gapi_client_id'],
                     "auth_uri":                      os.environ['gapi_auth_uri'],
                     "token_uri":                     os.environ['gapi_token_uri'],
                     "auth_provider_x509_cert_url":   os.environ['gapi_auth_provider_x509_cert_url'],
                     "client_x509_cert_url":          os.environ['gapi_client_x509_cert_url']}

        self.json = json.dumps(self.data)
        self.cred = json.loads(self.json)
        self.credentials = ServiceAccountCredentials.from_json_keyfile_dict(self.cred, self.scope)

        self.load_credentials()
        print('Accessor successfully connected')

    def load_credentials(self):
        # settings = open("config.json", "r")
        # credentials_file = json.load(settings)["ServiceAuthCredentials"]
        # self.credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self.scope)
        self.client = gspread.authorize(self.credentials)
        self.client.login()

        # reload the worksheets in the spreadsheets
        if len(self.SpreadsheetObjects.keys()) > 0:
            for spreadsheet in self.SpreadsheetObjects.keys():
                self.SpreadsheetObjects[spreadsheet]['object'] = self.client.open_by_url(self.SpreadsheetObjects[spreadsheet]['url'])

            for spreadsheet in self.SpreadsheetObjects.keys():
                worksheets = [x for x in self.SpreadsheetObjects[spreadsheet].keys() if x not in ['object', 'url']]
                for sheet in worksheets:
                    self.SpreadsheetObjects[spreadsheet][sheet] = self.SpreadsheetObjects[spreadsheet]['object'].worksheet(sheet)

    # End Initialization Methods

    # Connection to Spreadsheet/Worksheet Methods
    def open_spreadsheet(self, spreadsheet_name: str, spreadsheet_url: str):
        if spreadsheet_name in self.SpreadsheetObjects.keys():
            raise KeyError('{} already exists in dict SpreadsheetObjects'.format(spreadsheet_name))
        self.SpreadsheetObjects[spreadsheet_name] = {'object': self.client.open_by_url(spreadsheet_url), 'url': spreadsheet_url}

    def open_worksheet(self, spreadsheet_name: str, sheet_name: str):
        try:
            self.SpreadsheetObjects[spreadsheet_name][sheet_name] = self.SpreadsheetObjects[spreadsheet_name]['object'].worksheet(sheet_name)
        except KeyError as e:
            raise KeyError('{} key not found in SpreadsheetObjects'.format(e))
    # End Connection Methods

    # Data Accessing Methods
    def get_column_values(self, spreadsheet_name: str, worksheet_name: str, column: int, header_size=0, filtered=True):
        try:
            if filtered:
                return list(filter(None, self.SpreadsheetObjects[spreadsheet_name][worksheet_name].col_values(column)[header_size:]))
            else:
                return self.SpreadsheetObjects[spreadsheet_name][worksheet_name].col_values(column)[header_size:]
        except Exception as e:
            raise KeyError('{} key not found in SpreadsheetObjects'.format(e))

    def get_value(self, spreadsheet_name: str, worksheet_name: str, row: int, column: int):
        try:
            return self.SpreadsheetObjects[spreadsheet_name][worksheet_name].cell(row, column).value
        except Exception as e:
            raise KeyError('{} key not found in SpreadsheetObjects'.format(e))

    def get_row_values(self, spreadsheet_name: str, worksheet_name: str, row: int, header_size=0, filtered=True):
        try:
            if filtered:
                return list(filter(None, self.SpreadsheetObjects[spreadsheet_name][worksheet_name].row_values(row)[
                                         header_size:]))
            else:
                return self.SpreadsheetObjects[spreadsheet_name][worksheet_name].row_values(row)[header_size:]
        except Exception as e:
            print(self.SpreadsheetObjects.keys())
            raise KeyError('{} key not found in SpreadsheetObjects'.format(e))

    def set_value(self, spreadsheet_name: str, worksheet_name: str, value: str, row=None, column=None, cell=None):
        try:
            if cell is not None:
                self.SpreadsheetObjects[spreadsheet_name][worksheet_name].update_acell(cell, value)
            else:
                self.SpreadsheetObjects[spreadsheet_name][worksheet_name].update_cell(row, column, value)
        except Exception as e:
            if isinstance(e, KeyError):
                raise KeyError('{} key not found in SpreadsheetObjects'.format(e))
            else:
                raise Exception('Unhandled exception: ' + str(e))

    def write_range(self, spreadsheet_name: str, worksheet_name: str, start: tuple, end: tuple, iterable: list):
        first_cell = utils.rowcol_to_a1(start[0], start[1])
        last_cell = utils.rowcol_to_a1(end[0], end[1])
        cell_range = '{}:{}'.format(first_cell, last_cell)

        try:
            cells = self.SpreadsheetObjects[spreadsheet_name][worksheet_name].range(cell_range)
            for x, cell in enumerate(cells):
                cell.value = iterable[x]
            self.SpreadsheetObjects[spreadsheet_name][worksheet_name].update_cells(cells)
        except Exception as e:
            if isinstance(e, KeyError):
                raise KeyError('{} key not found in SpreadsheetObjects'.format(e))
            else:
                raise Exception('Unhandled exception: ' + str(e))

    def find_value(self, spreadsheet_name: str, worksheet_name: str, value: str):
        try:
            return self.SpreadsheetObjects[spreadsheet_name][worksheet_name].find(value)
        except Exception as e:
            if isinstance(e, KeyError):
                raise KeyError('{} key not found in SpreadsheetObjects'.format(e))
            else:
                raise Exception('Unhandled exception: ' + str(e))
    # End Data Accessing Methods

    # Utility Functions
    def get_current_time(self):
        return datetime.now(self.timezone).strftime('%H:%M:%S')

    @staticmethod
    def get_current_day():
        return '{}/{}/{}'.format(datetime.now().day, datetime.now().month, datetime.now().year)
