import time
import requests
import os
import processing

from .api_queries import crop_raster_query

from qgis.PyQt.QtWidgets import QApplication, QMessageBox

class Wapor3APIManager:
    """
        Class used to manage the API of WaPOR V3 and all its functions associated.

        ...

        Attributes
        ----------
        APIToken : String
            Token associated to the users account on WaPOR V3 platform.
        connected : bool
            If the plugin is currently connected to the WaPOR V3 database.
        sign_in_url : string
            URL prefix for sign into the WaPOR V3 database.
        query_url : string
            URL prefix for querying the WaPOR V3 database.
        catalog_url : string
            URL prefix for pulling the WaPOR V3 catalog.
        payload : Dict
            Dictionary with the payload of the query.
        time_out : int
            Seconds of waiting before claiming a time out.

        Methods
        -------
        signin(APIToken)
            Performs de sign in into the WaPOR V3 platform using the API token, and
            returns the state of the connection.
        isConnected():
            Returns if the API of WaPOR V3 is connected based in the sign in 
            function or an expired time event.
        query_crop_raster(params):
            Performs de crop and download raster query from the WaPOR V3 platform 
            using a dictionary with the parameters of the operation.
        query_listing(url):
            Performs de listing query for an URL which will return a list of
            elements in a catalog e.g workspaces, cubes, dimensions and measures.
        query_info(url):
            Performs de info query for an URL which will return the information
            of an specific element in the catalog e.g workspaces, cubes, 
            dimensions and measures.
        pull_workspaces():
            Pulls all the workspaces available in the catalog.
        get_info_workspace(workspace):
            Gets the information contained in the catalog with respect to a 
            given workspace code.
        pull_mapsets(workspace):
            Pulls all the pull_mapsets available in the catalog for a given workspace.
            
    """

    def __init__(self, APIToken=None):

        self.APIToken = APIToken
        self.connected =  False
        self.sign_in_url = r'https://data.apps.fao.org/gismgr/api/v2/catalog/identity/accounts:signInWithApiKey'
        # self.query_url = r'https://io.apps.fao.org/gismgr/api/v1/query/'
        self.catalog_url = r'https://data.apps.fao.org/gismgr/api/v2/catalog/'

        self.payload = {'overview':False,'paged':False}
        self.time_out = 5
    
    def showInternetMsg(self):
            print("The internet connection is down")
            QMessageBox.information(None, "No internet connection", '''<html><head/><body>
            <p>To interact with the WAPOR database a stable internet connection
            is required, you can still use the offline features.</p></body></html>''')
            return False
    
    def showServerDownMsg(self):
            print("The server is down")
            QMessageBox.information(None, "Server down", '''<html><head/><body>
            <p>Currently, the database server is facing issues. Please try again
            by restarting the plugin after some time.</p></body></html>''')
            return False
    
    def showCropErrorMsg(self, error_msg):
            print("Completed with errors [Crop raster]")
            QMessageBox.information(None, "Error in crop raster", '''<html><head/><body>
            <p>There was an error in the query on the query with FAO WAPOR portal:
            <br><br>
            ERROR: {}
            <br><br>
            Please check if the error is considered in our wiki page
            <a href="https://github.com/WAGIS/wap_plugin/wiki"><span style="text-decoration: 
            underline; color: #0000ff;">Wiki page</span></a>,
            if not please submit an 
            <a href="https://github.com/WAGIS/wap_plugin/issues"><span style="text-decoration: 
            underline; color: #0000ff;">issue</span></a>.</p></body></html>'''.format(error_msg))
            return False

    def signin(self, APIToken):
        """
            Performs de sign in into the WaPOR V3 platform using the API token, and
            returns the state of the connection.

            ...
            Parameters
            ----------
            APIToken : String
                Token associated to the users account on WaPOR V3 platform.
        """       
        request_headers = {'X-GISMGR-API-KEY': APIToken}

        try:
            resp = requests.post(self.sign_in_url, headers=request_headers)
            print('Connecting to WaPORv3 Database . . .')

            resp_json = resp.json()
            if resp_json['message'] == 'OK':
                self.AccessToken=resp_json['response']['idToken']
                self.RefreshToken=resp_json['response']['refreshToken']
                print('SUCCESS: Access granted')
                print('Access expires in {}'.format(resp_json['response']['expiresIn']))
                self.lastConnection_time = time.time()
                self.connected = True
                self.APIToken = APIToken
            else:
                print('Failed to connect to WaPOR V3 Database . . .')
                self.connected = False
        except requests.exceptions.ConnectionError:
            self.showInternetMsg()

        return self.connected

    def isConnected(self):
        """
            Returns if the API of WaPOR V3 is connected based in the sign in 
            function or an expired time event.
        """
        if not self.connected:
            return False
        elif time.time() - self.lastConnection_time > 3600:
            self.connected = False
        return self.connected

    def query_crop_raster(self, params):
        """
            Performs de crop and download raster query from the WaPOR V3 platform 
            using a dictionary with the parameters of the operation.

            ...
            Parameters
            ----------
            params : Dict
                Parameters of configuration for the query crop and download.

                properties['outputFileName'] : String
                    Path and name to the resulting raster file.
                cube['workspaceCode'] : String
                    Code of the workspace to which the raster belongs.
                cube['code'] : String
                    Code of the type of raster to download.
                dimensions : List
                    Definition of the List of time frames used to delimite the 
                    raster.
                measures : List
                    Definition of the List of measurements used to delimite the 
                    raster.
                shape['coordinates'] : List
                    List of points that defines the polygon of the raster.
                shape['crs'] : String
                    Reference system to define de coordinates.
        """
        pass
    
    def query_listing(self, urls):
        """
            Performs de listing query for an URL which will return a list of
            elements in a catalog e.g workspaces, cubes, dimensions and measures.

            ...
            Parameters
            ----------
            params : urls
                URLs to get listed from the query.
        """
        try:
            listing = dict()
            for url in urls:
                while url is not None:
                    try:
                        resp = requests.get(url,timeout=self.time_out).json()
                    except:
                        req_output = requests.get(url,timeout=self.time_out)
                        print('Connection failed due to {}: {}'.format(req_output.reason, req_output.status_code))
                        return -1
                    for elem in resp['response']['items']:
                        listing[elem['caption']] = elem['code']
                    url = resp['response']['links'][-1]['href'] if resp['response']['links'][-1]['rel'] == 'next' else None
            return listing
        except (requests.ConnectionError, requests.Timeout) as exception:
            print('requests.ConnectionError, requests.Timeout')
            print(exception)
            return None
        except (KeyError) as exception:
            print('KeyError')
            print(exception)
            return {'---':None}

    def query_info(self, url):
        """
            Performs de info query for an URL which will return the information
            of an specific element in the catalog e.g workspaces, cubes, 
            dimensions and measures.

            ...
            Parameters
            ----------
            url : String
                URL to get the info from the query.
        """
        try:
            resp = requests.get(url,timeout=self.time_out).json()
            return resp['response']
        except (requests.ConnectionError, requests.Timeout) as exception:
            return None

    def pull_workspaces(self):
        """
            Pulls all the workspaces available in the catalog.
        """
        workspaces_url = self.catalog_url+'workspaces'
        workspaces_dict = self.query_listing([workspaces_url])
        if workspaces_dict is None:
            self.showInternetMsg()
            return {}
            # raise Exception("Query [pull_workspaces] error, no internet connection or timeout")
        elif workspaces_dict == -1:
            self.showServerDownMsg()
            return {}
        else:
            return workspaces_dict
        
    def get_info_workspace(self, workspace):
        """
            Gets the information contained in the catalog with respect to a 
            given workspace code.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to get the info from the query.
        """
        workspace_url = self.catalog_url+'workspaces/{}'.format(workspace)
        workspace_resp = self.query_info(workspace_url)
        if workspace_resp is None:
            raise Exception("Query [info_workspaces] error, no internet connection or timeout")
        else:
            return workspace_resp['caption'], workspace_resp['description']
        
    def pull_mapsets(self, workspace):
        mapsets_url = self.catalog_url+'workspaces/{}/mapsets'.format(workspace)
        mosaicsets_url = self.catalog_url+'workspaces/{}/mosaicsets'.format(workspace)
        
        mapsets_dict = self.query_listing([mapsets_url, mosaicsets_url])
        if mapsets_dict is None:
            self.showInternetMsg()
            return {}
        else:
            return mapsets_dict
        
    def query_rasters(self, url):
        """
            Performs de listing of the rasters to get all the information from its
            URL TODO to be completed.

            ...
            Parameters
            ----------
            params : url
                URL of the raster to get listed from the query.
        """
        try:
            listing = dict()
            while url is not None:
                resp = requests.get(url,timeout=self.time_out).json()
                for elem in resp['response']['items']:
                    listing[elem['code']] = elem['downloadUrl']
                url = resp['response']['links'][-1]['href'] if resp['response']['links'][-1]['rel'] == 'next' else None
            return listing
        except (requests.ConnectionError, requests.Timeout) as exception:
            print('requests.ConnectionError, requests.Timeout')
            print(exception)
            return None
        except (KeyError) as exception:
            print('KeyError')
            print(exception)
            return {'---':None}
        
    def pull_rasters(self, workspace, mapset):
        rasters_url = self.catalog_url+'workspaces/{}/mapsets/{}/rasters'.format(workspace, mapset)
        
        rasters_dict = self.query_rasters(rasters_url)
        if rasters_dict is None:
            self.showInternetMsg()
            return {}
        else:
            return rasters_dict

class Wapor2APIManager:
    """
        Class used to manage the API of WaPOR V2 and all its functions associated.

        ...

        Attributes
        ----------
        APIToken : String
            Token associated to the users account on WaPOR V2 platform.
        connected : bool
            If the plugin is currently connected to the WaPOR V2 database.
        sign_in_url : string
            URL prefix for sign into the WaPOR V2 database.
        query_url : string
            URL prefix for querying the WaPOR V2 database.
        catalog_url : string
            URL prefix for pulling the WaPOR V2 catalog.
        payload : Dict
            Dictionary with the payload of the query.
        time_out : int
            Seconds of waiting before claiming a time out.

        Methods
        -------
        signin(APIToken)
            Performs de sign in into the WaPOR V2 platform using the API token, and
            returns the state of the connection.
        isConnected():
            Returns if the API of WaPOR V2 is connected based in the sign in 
            function or an expired time event.
        query_crop_raster(params):
            Performs de crop and download raster query from the WaPOR V2 platform 
            using a dictionary with the parameters of the operation.
        query_listing(url):
            Performs de listing query for an URL which will return a list of
            elements in a catalog e.g workspaces, cubes, dimensions and measures.
        query_info(url):
            Performs de info query for an URL which will return the information
            of an specific element in the catalog e.g workspaces, cubes, 
            dimensions and measures.
        pull_workspaces():
            Pulls all the workspaces available in the catalog.
        get_info_workspace(workspace):
            Gets the information contained in the catalog with respect to a 
            given workspace code.
        pull_cubes(workspace):
            Pulls all the cubes available in the catalog for a given workspace.
            
        get_info_cube(workspace, cube):
            Gets the information contained in the catalog with respect to a 
            given set of workspace and cube codes.
        pull_cube_dims(workspace, cube):
            Pulls all the dimensions available in the catalog for a given set of
            workspace and cube codes.
        get_info_cube_dim(workspace, cube, dimension):
            Gets the information contained in the catalog with respect to a 
            given set of workspace, cube and dimension codes.
        pull_cube_dim_membs(workspace, cube, dimension):
            Pulls all the members available in the catalog for a given set of
            workspace, cube and dimension codes.
        get_info_cube_dim_memb(workspace, cube, dimension, member):
            Gets the information contained in the catalog with respect to a 
            given set of workspace, cube, dimension and member codes.
        pull_cube_meas(workspace, cube):
            Pulls all the measures available in the catalog for a given set of
            workspace and cube codes.
        get_info_cube_mea(workspace, cube, measure):
            Gets the information contained in the catalog with respect to a 
            given set of workspace and cube codes.
    """

    def __init__(self, APIToken=None):

        self.APIToken = APIToken
        self.connected =  False
        self.sign_in_url = r'https://io.apps.fao.org/gismgr/api/v1/iam/sign-in/'
        self.query_url = r'https://io.apps.fao.org/gismgr/api/v1/query/'
        self.catalog_url = r'https://io.apps.fao.org/gismgr/api/v1/catalog/'

        self.payload = {'overview':False,'paged':False}
        self.time_out = 5
    
    def showInternetMsg(self):
            print("The internet connection is down")
            QMessageBox.information(None, "No internet connection", '''<html><head/><body>
            <p>To interact with the WAPOR database a stable internet connection
            is required, you can still use the offline features.</p></body></html>''')
            return False

    def showCropErrorMsg(self, error_msg):
            print("Completed with errors [Crop raster]")
            QMessageBox.information(None, "Error in crop raster", '''<html><head/><body>
            <p>There was an error in the query on the query with FAO WAPOR portal:
            <br><br>
            ERROR: {}
            <br><br>
            Please check if the error is considered in our wiki page
            <a href="https://github.com/WAGIS/wap_plugin/wiki"><span style="text-decoration: 
            underline; color: #0000ff;">Wiki page</span></a>,
            if not please submit an 
            <a href="https://github.com/WAGIS/wap_plugin/issues"><span style="text-decoration: 
            underline; color: #0000ff;">issue</span></a>.</p></body></html>'''.format(error_msg))
            return False

    def signin(self, APIToken):
        """
            Performs de sign in into the WaPOR v2 platform using the API token, and
            returns the state of the connection.

            ...
            Parameters
            ----------
            APIToken : String
                Token associated to the users account on WaPOR v2 platform.
        """       
        request_headers = {'X-GISMGR-API-KEY': APIToken}

        try:
            resp = requests.post(self.sign_in_url, headers=request_headers)
            print('Connecting to WaPOR v2 Database . . .')

            resp_json = resp.json()
            if resp_json['message'] == 'OK':
                self.AccessToken=resp_json['response']['accessToken']
                print('SUCCESS: Access granted')
                print('Access expires in 3600s')
                self.lastConnection_time = time.time()
                self.connected = True
                self.APIToken = APIToken
            else:
                print('Failed to connect to WaPOR v2 Database . . .')
                self.connected = False
        except requests.exceptions.ConnectionError:
            self.showInternetMsg()

        return self.connected

    def isConnected(self):
        """
            Returns if the API of WaPOR v2 is connected based in the sign in 
            function or an expired time event.
        """
        if not self.connected:
            return False
        elif time.time() - self.lastConnection_time > 3600:
            self.connected = False
        return self.connected

    def query_crop_raster(self, params, downloadButton):
        """
            Performs de crop and download raster query from the WaPOR v2 platform 
            using a dictionary with the parameters of the operation.

            ...
            Parameters
            ----------
            params : Dict
                Parameters of configuration for the query crop and download.

                properties['outputFileName'] : String
                    Path and name to the resulting raster file.
                cube['workspaceCode'] : String
                    Code of the workspace to which the raster belongs.
                cube['code'] : String
                    Code of the type of raster to download.
                dimensions : List
                    Definition of the List of time frames used to delimite the 
                    raster.
                measures : List
                    Definition of the List of measurements used to delimite the 
                    raster.
                shape['coordinates'] : List
                    List of points that defines the polygon of the raster.
                shape['crs'] : String
                    Reference system to define de coordinates.
            downloadButton : QT.Button
                Download button to disable multiple requests.
        """
        if not self.isConnected():
            raise Exception("Query [crop_raster] error, no WaPOR v2 connection")
        else:
            request_json = crop_raster_query.copy()
            request_json['params']['properties']['outputFileName'] = params['outputFileName']
            request_json['params']['cube']['workspaceCode'] = params['cube_workspaceCode']
            request_json['params']['cube']['code'] = params['cube_code']
            request_json['params']['dimensions'] = params['dimensions']
            request_json['params']['measures'] = params['measures']

            print("Dimensions: ", request_json['params']['dimensions'])
            if params['coordinates'][0] is not None:
                request_json['params']['shape']['coordinates'] = params['coordinates']
                request_json['params']['shape']['crs'] = params['crs']
            else:
                print('WARNING: Valid coordinates not provided, using default ones . . . ')
            
            request_headers = {'Authorization': "Bearer " + self.AccessToken}

            try:
                resp_json = requests.post(  self.query_url,
                                            json=request_json,
                                            headers=request_headers).json()
                if resp_json['message']=='OK':
                    job_url = resp_json['response']['links'][0]['href']
                    downloadButton.setEnabled(False)

                    while True:
                        QApplication.processEvents()
                        response = requests.get(job_url)
                        resp_json=response.json()
                        # NOTE: Uncomment if needed to check status
                        # print(resp_json['response']['status'])
                        if resp_json['response']['status']=='COMPLETED':
                            rast_url = resp_json['response']['output']['downloadUrl']
                            return rast_url
                        elif resp_json['response']['status']=='COMPLETED WITH ERRORS':
                            log_resp = resp_json['response']['log'][-3:-1]
                            print(log_resp)
                            self.showCropErrorMsg(log_resp[-1].split('ERROR: ')[-1])
                            return None
                        elif resp_json['response']['status'] == 'WAITING' or resp_json['response']['status'] == 'RUNNING':
                            pass
                        else:
                            raise Exception("Query [crop_raster] error status not handled")
            except requests.exceptions.ConnectionError:
                self.showInternetMsg()

            else:
                #  TODO raise something
                print('Fail to get job url')
    
    def query_listing(self, url):
        """
            Performs de listing query for an URL which will return a list of
            elements in a catalog e.g workspaces, cubes, dimensions and measures.

            ...
            Parameters
            ----------
            params : url
                URL to get listed from the query.
        """
        try:
            resp = requests.get(url,self.payload,timeout=self.time_out).json()

            listing = dict()
            for elem in resp['response']:
                listing[elem['caption']] = elem['code']
            return listing
        except (requests.ConnectionError, requests.Timeout) as exception:
            print(exception)
            return None
        except (KeyError) as exception:
            print(exception)
            return {'---':None}

    def query_info(self, url):
        """
            Performs de info query for an URL which will return the information
            of an specific element in the catalog e.g workspaces, cubes, 
            dimensions and measures.

            ...
            Parameters
            ----------
            url : String
                URL to get the info from the query.
        """
        try:
            resp = requests.get(url,timeout=self.time_out).json()
            return resp['response']
        except (requests.ConnectionError, requests.Timeout) as exception:
            return None

    def pull_workspaces(self):
        """
            Pulls all the workspaces available in the catalog.
        """
        workspaces_url = self.catalog_url+'workspaces'
        workspaces_dict = self.query_listing(workspaces_url)
        if workspaces_dict is None:
            self.showInternetMsg()
            return {}
            # raise Exception("Query [pull_workspaces] error, no internet connection or timeout")
        else:
            return workspaces_dict
        
    def get_info_workspace(self, workspace):
        """
            Gets the information contained in the catalog with respect to a 
            given workspace code.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to get the info from the query.
        """
        workspace_url = self.catalog_url+'workspaces/{}'.format(workspace)
        workspace_resp = self.query_info(workspace_url)
        if workspace_resp is None:
            raise Exception("Query [info_workspaces] error, no internet connection or timeout")
        else:
            return workspace_resp['caption'], workspace_resp['description']

    def pull_cubes(self, workspace):
        """
            Pulls all the cubes available in the catalog for a given workspace.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code from which the query will pull the cubes.
        """
        timeOptions = set()
        countryOptions = set()
        levelOptions = set()

        cubes_url = self.catalog_url+'workspaces/{}/cubes'.format(workspace)
        cubes_dict = self.query_listing(cubes_url)
        if cubes_dict is None:
            self.showInternetMsg()
            return {}, [], [], []
            # raise Exception("Query [pull_cubes] error, no internet connection or timeout")
        else:
            keys2remove = list()
            for cube_key, cube_value in cubes_dict.items():
                temp = cube_value.split("_")
                cube_level = temp[0]
                values_dict = {'id':cube_value,'time':None, 'country':None, 'level':cube_level}
                levelOptions.add(cube_level)

                # import json
                # info =  self.get_info_cube(workspace, cube_value)
                # print(json.dumps(info, indent=2))
                # input()
                
                if workspace == 'WAPOR_2':
                    if 'clipped' in cube_key:
                        keys2remove.append(cube_key)
                    if '-' in cube_key:
                        temp = cube_key.split(" - ")
                        cube_time = temp[-1].replace(')','')
                        cube_country = temp[-2].split(", ")[-1]
                        values_dict['time'] = cube_time
                        values_dict['country'] = cube_country
                        timeOptions.add(cube_time)
                        countryOptions.add(cube_country)

                    if cube_level == 'L1' or cube_level == 'L2':
                        values_dict['time'] = cube_key.split(" (")[-1].split(")")[0]
                cubes_dict[cube_key] = values_dict


            for key in keys2remove:
                cubes_dict.pop(key, None)

            return cubes_dict, list(sorted(timeOptions)), list(sorted(countryOptions)), list(sorted(levelOptions))
    
    def filter_cubes(self, unfilteredCubes, filters, mode):
        filteredCubes = list()

        if mode == 'pos':
            keys2remove = list()
            for filter_key, filter_value in filters.items():
                if filter_value == 'None':
                    keys2remove.append(filter_key)
            for key in keys2remove:
                    filters.pop(key, None)
            for cube_key, cube_dict in unfilteredCubes.items():
                addFlag = False
                for filter_key, filter_value in filters.items():
                    if filter_value == cube_dict[filter_key]:
                        addFlag = True
                    else:
                        addFlag = False
                        break
                """ Below two lines are added temorarily. TODO: Fix download of Phenology data """
                if 'phenology' in str(cube_key).lower():
                    addFlag = False
                if addFlag:   
                    filteredCubes.append(cube_key)
                    
        elif mode == 'neg':
            for cube in unfilteredCubes.keys():
                addFlag = True
                for filter_out in filters:
                    if filter_out in cube:
                        addFlag = False
                if addFlag:    
                    filteredCubes.append(cube)
                    
        return filteredCubes
    
    def get_info_cube(self, workspace, cube):
        """
            Gets the information contained in the catalog with respect to a 
            given set of workspace and cube codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code to get the info from the query.
        """
        cube_url = self.catalog_url+'workspaces/{}/cubes/{}'.format(workspace,cube)
        cube_resp = self.query_info(cube_url)
        if cube_resp is None:
            self.showInternetMsg()
            return '', ''
            # raise Exception("Query [info_cube] error, no internet connection or timeout")
        else:
            return cube_resp['caption'], cube_resp['description']
    
    def pull_cube_info(self, workspace, cube):
        """
            Pulls all the relevant information about the cube
            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code from which the query will pull the dimensions.
        """   
        info_list = list()
        cubes_url = self.catalog_url+'workspaces/{}/cubes/{}'.format(workspace,cube)
        try:
            resp_ele = requests.get(cubes_url, self.payload, timeout=self.time_out).json()
        except (requests.ConnectionError, requests.Timeout) as exception:
            print(exception)

        info_list.append({"type": "Caption", "details": resp_ele['response']['caption']})
        info_list.append({"type": "Description", "details": resp_ele['response']['description']})

        additional_info = resp_ele['response']['additionalInfo']  
        for info_key, info_value in additional_info.items():
            info_list.append({"type": info_key, "details": info_value})
        
        return info_list

    def pull_cube_dims(self, workspace, cube):
        """
            Pulls all the dimensions available in the catalog for a given set of
            workspace and cube codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code from which the query will pull the dimensions.
        """
        cube_dims_url = self.catalog_url+'workspaces/{}/cubes/{}/dimensions'.format(workspace,cube)
        cube_dims_dict = self.query_listing(cube_dims_url)
        if cube_dims_dict is None:
            self.showInternetMsg()
            return {}
            # raise Exception("Query [pull_cube_dims] error, no internet connection or timeout")
        else:
            return cube_dims_dict

    def get_info_cube_dim(self, workspace, cube, dimension):
        """
            Gets the information contained in the catalog with respect to a 
            given set of workspace, cube and dimension codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code to which the dimension belongs.
            dimension : String
                Dimension code to get the info from the query.
        """
        cube_dim_url = self.catalog_url+'workspaces/{}/cubes/{}/dimensions/{}'.format(workspace,cube,dimension)
        cube_dim_resp = self.query_info(cube_dim_url)
        if cube_dim_resp is None:
            self.showInternetMsg()
            return '', ''
            # raise Exception("Query [info_cube_dim] error, no internet connection or timeout")
        else:
            return cube_dim_resp['caption'], cube_dim_resp['description']

    def pull_cube_dim_membs(self, workspace, cube, dimension):
        """
            Pulls all the members available in the catalog for a given set of
            workspace, cube and dimension codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code to which the dimension belongs.
            dimension : String
                Dimension code from which the query will pull the members.
        """
        cube_dim_membs_url = self.catalog_url+'workspaces/{}/cubes/{}/dimensions/{}/members'.format(workspace,cube,dimension)
        cube_dim_membs_dict = self.query_listing(cube_dim_membs_url)
        if cube_dim_membs_dict is None:
            self.showInternetMsg()
            return {}
            # raise Exception("Query [pull_cube_dim_membs] error, no internet connection or timeout")
        else:
            return cube_dim_membs_dict

    def get_info_cube_dim_memb(self, workspace, cube, dimension, member):
        """
            Gets the information contained in the catalog with respect to a 
            given set of workspace, cube, dimension and member codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code to which the dimension belongs.
            dimension : String
                Dimension code to which the Member belongs.
            member : String
                Member code to get the info from the query.
        """
        cube_dim_memb_url = self.catalog_url+'workspaces/{}/cubes/{}/dimensions/{}/members/{}'.format(workspace,cube,dimension,member)
        cube_dim_memb_resp = self.query_info(cube_dim_memb_url)
        if cube_dim_memb_resp is None:
            self.showInternetMsg()
            return '', ''
            # raise Exception("Query [info_cube_dim_memb] error, no internet connection or timeout")
        else:
            return cube_dim_memb_resp['caption'], cube_dim_memb_resp['description']

    def pull_cube_meas(self, workspace, cube):
        """
            Pulls all the measures available in the catalog for a given set of
            workspace and cube codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code from which the query will pull the measures.
        """
        cube_meas_url = self.catalog_url+'workspaces/{}/cubes/{}/measures'.format(workspace,cube)
        cube_meas_dict = self.query_listing(cube_meas_url)
        if cube_meas_dict is None:
            self.showInternetMsg()
            return {}
            # raise Exception("Query [pull_cube_meas] error, no internet connection or timeout")
        else:
            return cube_meas_dict

    def get_info_cube_mea(self, workspace, cube, measure):
        """
            Gets the information contained in the catalog with respect to a 
            given set of workspace and cube codes.

            ...
            Parameters
            ----------
            workspace : String
                Workspace code to which the cube belongs.
            cube : String
                Cube code to which the dimension belongs.
            measure : String
                Measure code to get the info from the query.
        """
        cube_meas_url = self.catalog_url+'workspaces/{}/cubes/{}/measures/{}'.format(workspace,cube,measure)
        cube_meas_resp = self.query_info(cube_meas_url)
        if cube_meas_resp is None:
            self.showInternetMsg()
            return '', ''
            # raise Exception("Query [info_cube_meas] error, no internet connection or timeout")
        else:
            return cube_meas_resp['caption'], cube_meas_resp['description']


class FileManager:
    """
        Class used to manage the files in the workspace of the plugin.

        ...

        Attributes
        ----------
        plugin_dir : String
            Path of the plugin workspace in the system.
        rasters_dir : String
            Path of the rasters workspace in the system.

        Methods
        -------
        check_path(path):
            Checks if a path exists system.
        create_path(path):
            Creates a path in the system if it does not exist.
        list_rasters(rasters_path):
            Returns a list of raster files contained in a path of the system if
            the path exist, otherwise it will create the path.
        download_raster(rast_url):
            Downloads a raster file into the systems memory from an URL.
        save_token(APIToken):
            Saves into the systems memory a file with the token associated to a
            WaPOR account.
        load_token():
            Loads from the file in the systems memory the token associated to a
            WaPOR account.
        filterRasterFiles(files, raster_types):
            Filters the raster files in the systems memory based on a type.
    """
    def __init__(self, plugin_dir, rasters_path):
        self.plugin_dir = plugin_dir
        self.rasters_dir = os.path.join(self.plugin_dir, rasters_path)

    def check_path(self, path):
        """
            Checks if a path exists system.

            ...
            Parameters
            ----------
            path : String
                Path to be checked.
        """
        dir = os.path.join(self.plugin_dir,path)
        return os.path.exists(dir)

    def create_path(self, path):
        """
            Creates a path in the system if it does not exist.

            ...
            Parameters
            ----------
            path : String
                Path to be created.
        """
        dir = os.path.join(self.plugin_dir,path)
        if not os.path.exists(dir):
            os.mkdir(dir)
        else:
            print('The path [{}] is already in the workspace'.format(path))

    def list_rasters(self, rasters_folder):
        """
            Returns a list of raster files contained in a path of the system if
            the path exist, otherwise it will create the path.

            ...
            Parameters
            ----------
            rasters_path : String
                Path from where the raster files will be listed with respect to
                the plugin absolute path.
        """
        tif_files_dict = dict()
        if os.path.exists(rasters_folder):
            for dirpath, _, fnames in os.walk(rasters_folder):
                for file in fnames:
                    if file.endswith(".tif"):
                        tif_files_dict[file] = os.path.join(dirpath, file)
            print('Found {} layers in the workspace [{}]'.format(len(tif_files_dict),rasters_folder))
        else:
            self.create_path(rasters_folder)
        return tif_files_dict

    def download_raster(self, rast_url, rast_directory):
        """
            Downloads a raster file into the systems memory from an URL.

            ...
            Parameters
            ----------
            rast_url : String
                Download URL of the raster file.
        """
        file_name = rast_url.rsplit('/', 1)[1]
        file_dir = os.path.join(rast_directory, file_name)

        #TODO Check if file already exist

        parameter_dictionary = {
                                    'URL' : rast_url,
                                    'OUTPUT' : file_dir
                                }
                                
        processing.run("qgis:filedownloader", parameter_dictionary)

        while True:
            QApplication.processEvents()
            if os.path.isfile(file_dir):
                print('File in workspace')
                break

    def save_token(self, APIToken):
        """
            Saves into the systems memory a file with the token associated to a
            WaPOR account.

            ...
            Parameters
            ----------
            APIToken : String
                Token associated to a WaPOR account.
        """
        tokendir = os.path.join(self.plugin_dir,'apitoken.token')
        with open(tokendir, 'w') as tokenFile:
            tokenFile.write(APIToken)

    def load_token(self):
        """
            Loads from the file in the systems memory the token associated to a
            WaPOR account.
        """
        tokendir = os.path.join(self.plugin_dir,'apitoken.token')
        if os.path.isfile(tokendir):
            with open(tokendir, 'r') as tokenFile:
                APIToken = tokenFile.read()
                print(APIToken)
                return APIToken
        else:
            return None

    def filterRasterFiles(self, files, raster_types):
        """
            Filters the raster files in the systems memory based on a type.

            ...
            Parameters
            ----------
            files : List
                Token associated to a WaPOR account.
            raster_types : List
                List of strings with the code of raster types to filter out.
        """
        filteredRasterFiles = dict()
        for name, path in files.items():
            for raster_type in raster_types:
                header = os.path.splitext(name)[0]
                roots = header.split('_')
                roots_2 = header.split('-')
                if raster_type in roots or raster_type in roots_2:
                    filteredRasterFiles[name] = path

        return filteredRasterFiles

class CanvasManager:
    """
        Class used to manage the files in the workspace of the plugin.

        ...

        Attributes
        ----------
        plugin_dir : String
            Path of the plugin workspace in the system.
        rasters_dir : String
            Path of the rasters workspace in the system.
        iface : QgsInterface
            Interface instance to manipulate the QGIS application at run time.

        Methods
        -------
        check_path(path):
            Checks if a path exists system.
    """
    def __init__(self, interface, plugin_dir, rasters_path):
        self.iface = interface
        self.plugin_dir = plugin_dir
        self.rasters_dir = os.path.join(self.plugin_dir,rasters_path)

    def add_rast(self, raster_name):
        """
            Includes the raster given from memory into the canvas of QGIS.

            ...
            Parameters
            ----------
            raster_name : String
                Name of the raster file in the systems memory to be included
                in the canvas.
        """
        raster_dir = os.path.join(self.rasters_dir,raster_name)
        if not self.iface.addRasterLayer(raster_dir,raster_name):
            print("Layer failed to load raster [{}]".format(raster_name))
            return False
        return True
    
    def set_rasters_dir(self, dir):
        self.rasters_dir = dir

    def rm_rast(self, raster):
        raise NotImplementedError("Canvar Manager, Remove raster not implemented.")

