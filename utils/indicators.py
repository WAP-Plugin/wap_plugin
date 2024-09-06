"""
    Indicator computation and additional resources and respective links for computation

    - Some common operation with QGIS
        https://docs.qgis.org/3.10/en/docs/pyqgis_developer_cookbook/raster.html
    - A python library to convert raster to numpy array
        https://geoscripting-wur.github.io/PythonRaster/
    - Using python library gdal
        https://www.youtube.com/watch?v=Rv8v9HPVq9M
    - Using Notbook for computations after converting to python array
        https://github.com/wateraccounting/WAPORWP/blob/master/Notebooks/Module_3_CalculatePerformanceIndicators.ipynb

"""
import numpy as np
from osgeo import gdal
import os

from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
from qgis.core import QgsRasterLayer

from qgis.PyQt.QtWidgets import QMessageBox


"""
    '<NAME_INDICATOR>' : {
        'info' : '<FORMULA_TO_COMPUTE_THE_INDICATOR>',
        'rasters' : { 
            # Pairs code and name of the rasters used 
            '<CODE_RASTER_1>' : '<NAME_RASTER_1>',
            '<CODE_RASTER_2>' : '<NAME_RASTER_2>',
            .
            .
            .
            '<CODE_RASTER_N>' : '<NAME_RASTER_N>' 
        },
        'factors' : {
            # Coeficients used in the formula, might or might not be provided
            # by the user through the UI
            'FACTOR_1' : 'DESCRIPTION_FACTOR_1',
            'FACTOR_2' : 'DESCRIPTION_FACTOR_2',
            .
            .
            .
            'FACTOR_N' : 'DESCRIPTION_FACTOR_N'
        },
        'params' : {
            # Parameters to be readed from the UI
            'PARAM_1' : {'label':'AETI or PE', 'type': ['AETI','PE']},
            'PARAM_2' : '',
            'PARAM_3' : ''
        }
"""

INDICATORS_INFO = {
                    'Uniformity of Water Consumption' : {
                        'info' : 'Equity is defined as the coefficients of variation (CV) of seasonal ETa in the area of interest.  \
                                  equity = (sd_raster / mean_raster) * 100',
                        'rasters' : {
                            'AETI' : 'Actual Evapotranspiration and Interception'
                        },
                        'factors' : {
                            'sd_raster' : 'Standard deviation obtained from the Raster',
                            'mean_raster' : 'Mean obtained from the Raster'
                        },
                        'params' : {
                            'PARAM_1' : {'label':'AETI', 'type': ['AETI']},
                            'PARAM_2' : '',
                            'PARAM_3' : ''
                        }
                    },
                    'Beneficial Fraction' : {
                        'info' : 'BF = (T / AETI)',
                        'rasters' : {
                            'AETI' : 'Actual Evapotranspiration and Interception',
                            'T' : 'Transpiration'
                        },
                        'factors' : {
                            # 'Conversion Factor' : '0.1'
                        },
                        'params' : {
                            'PARAM_1' : {'label':'T Raster', 'type': ['T']},
                            'PARAM_2' : {'label':'AETI Raster', 'type': ['AETI']},
                            'PARAM_3' : ''
                        }
                    },
                    'Adequacy (Relative Evapotranspiration)' : {
                        'info' : 'AD = (ETa / ETp)',
                        'rasters' : {
                            'ETa' : 'Actual Evapotranspiration and Interception',
                            'ETp' : '95th percentile of AETI '
                        },
                        'factors' : {
                            # 'Kc' : 'A constant to compute Potential Evapotranspiration'
                        },
                        'params' : {
                            'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                            'PARAM_2' : '',
                            'PARAM_3' : ''
                        }
                    },
                    'Relative Water Deficit' : {
                        'info' : 'RWD = 1 - (AETI / ETx)',
                        'rasters' : {
                            'AETI' : 'Actual Evapotranspiration and Interception'
                        },
                        'factors' : {
                            'ETx' : '99 percentile of the Raster'
                        },
                        'params' : {
                            'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                            'PARAM_2' : '',
                            'PARAM_3' : ''
                        }
                    },
                    'Total Biomass Production' : {
                        'info' : """Net Primary Production can be used to estimate total biomass production using the following formula:  \n TBP = (NPP * 22.22)/1000 
                        \n The value 22.222 is to convert the NPP in gC/m^2 to biomass production in kg/ha. To convert to ton/ha the value is divided by 1000.""",
                        'rasters' : {
                            'NPP' : 'Net Primary Production'
                        },
                        'factors' : {
                        },
                        'params' : {
                            'PARAM_1' : {'label':'NPP Raster', 'type': ['NPP']},
                            'PARAM_2' : '',
                            'PARAM_3' : ''
                        }
                    },
                    'Biomass Water Productivity' : {
                        'info' : """It is defined as the total biomass production divided by the AETI:  \n WPb = TBP/AETI * 100
                        \n The multiplication with 100 is needed to correct the units, first convert TBP in ton/ha to kg/m^2 (divide by 10) and then AETI from mm/season to m/season (divide by 1000) so that the final unit of WPb is kg/m^3.""",
                        'rasters' : {
                            'AETI' : 'Actual Evapotranspiration and Interception',
                            'TBP' : 'Total Biomass Productionn'
                        },
                        'factors' : {
                        },
                        'params' : {
                            'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                            'PARAM_2' : {'label':'TBP Raster', 'type': ['TBP']},
                            'PARAM_3' : ''
                        }
                    },
                    'Yield' : {
                        'info' : """Yield Y = HI * AOT * fc * (TBP / (1 - MC)) \n MC: moisture content, dry matter over fresh biomass \n fc: Light use efficiency correction factor \n AOT: above ground over total biomass production ratio(AOT) \n HI: Harvest Index""",
                        'rasters' : {
                            'TBP' : 'Total Biomass Productionn'
                        },
                        'factors' : {
                        },
                        'params' : {
                            'PARAM_1' : {'label':'TBP Raster', 'type': ['TBP']},
                            'PARAM_2' : '',
                            'PARAM_3' : ['MC', 'fc', 'AOT', 'HI']
                        }
                    },
                    'Crop Water Productivity' : {
                        'info' : """It is defined as the yield divided by the AETI:  \n cWP = Y/AETI * 100
                        \n The multiplication with 100 is to correct the units to kg/m3 (from AETI in mm/season and TBP in ton/ha) .""",
                        'rasters' : {
                            'Y' : 'Yield',
                            'AETI' : 'Actual Evapotranspiration and Interception'
                        },
                        'factors' : {
                        },
                        'params' : {
                            'PARAM_1' : {'label':'Y Raster', 'type': ['Y']},
                            'PARAM_2' : {'label':'AETI Raster', 'type': ['AETI']},
                            'PARAM_3' : ''
                        }
                    },
                    # """ Below indicators are commented out because they still have to be validated """
                    # 'Overall Consumed Ratio' : {
                    #     'info' : 'OCR = (AETI - PCP) / V_ws',
                    #     'rasters' : {
                    #         'AETI' : 'Actual Evapotranspiration and Interception',
                    #         'PCP' : 'Precipitation'
                    #     },
                    #     'factors' : {
                    #         'V_ws' : 'Volume of water supplied to command area in mm.'
                    #     },
                    #     'params' : {
                    #         'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                    #         'PARAM_2' : {'label':'PCP Raster', 'type': ['PCP']},
                    #         'PARAM_3' : 'V_ws'
                    #     }
                    # },
                    # 'Field Application Ratio (efficiency)' : {
                    #     'info' : 'FAR = (AETI - PCP) / V_wd',
                    #     'rasters' : {
                    #         'AETI' : 'Actual Evapotranspiration and Interception',
                    #         'PCP' : 'Precipitation'
                    #     },
                    #     'factors' : {
                    #         'V_wd' : 'Volume of water delivered to field(s) in mm.'
                    #     },
                    #     'params' : {
                    #         'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                    #         'PARAM_2' : {'label':'PCP Raster', 'type': ['PCP']},
                    #         'PARAM_3' : 'V_wd'
                    #     }
                    # },
                    # 'Depleted Fraction' : {
                    #     'info' : 'DF = 1 - AETI / (PCP + V_c)',
                    #     'rasters' : {
                    #         'AETI' : 'Actual Evapotranspiration and Interception',
                    #         'PCP' : 'Precipitation'
                    #     },
                    #     'factors' : {
                    #         'V_c' : 'Volume of water consumed in mm.'
                    #     },
                    #     'params' : {
                    #         'PARAM_1' : {'label':'AETI Raster', 'type': ['AETI']},
                    #         'PARAM_2' : {'label':'PCP Raster', 'type': ['PCP']},
                    #         'PARAM_3' : 'V_c'
                    #     }
                    # }
                  }

class IndicatorCalculator:
    def __init__(self, plugin_dir, rasters_path):
        self.plugin_dir = plugin_dir
        self.rasters_dir = os.path.join(self.plugin_dir, rasters_path)

    def setRastersDir(self, newPath):
        self.rasters_dir = os.path.join(self.plugin_dir, newPath)

    def showErrorMsg(self, msg):
        print("The internet connection is down")
        QMessageBox.information(None, "Calculation error", '''<html><head/><body>
        <p>{}.</p></body></html>'''.format(msg))

    def equity(self, raster, outLabel):
        """
        [FORMULA PASSED THE TEST WITH TRUE VALUES]
        Equity is computed from the formula:
            --- equity = 0.1 * (AETIsd / AETImean) * 100
            --- Resolution: Continental, National, Sub-national 
            where:
                -- AETIsd - (real number) - Standard deviation obtained from a Raster:
                --- Formula: AETIsd = Standard deviation of a Raster 
                --- Raster Types: AETI, PE, ACB
                --- Conversion Factor: AETI - 0.1, PE - 0.01, ACB - 50
                -- AETImean - (real number) - Mean obtained from a Raster
                    --- Formula: AETIsd = Mean of a Raster
                        --- Raster Types: AETI, PE
                        --- Conversion Factor: AETI - 0.1, PE - 0.01
                --- 0.1 - (real number) - Unit conversion factor because the rasters are in different unit from Wapor

        Output:
        --- equity - real number
        """
        ras_atei_dir = os.path.join(self.rasters_dir, raster)
        print('test equity')
        print(self.rasters_dir)
        print(ras_atei_dir)
        print(raster)
        ds = gdal.Open(ras_atei_dir)

        atei_band1 = self._get_array(ds)

        AETIm   = np.nanmean(atei_band1)
        AETIsd  = np.nanstd(atei_band1)

        equity = (AETIsd / AETIm) * 100

        if equity < 10:
            U = 'Good Uniformity'
        elif 10 <= equity < 25:
            U = 'Fair Uniformity'
        else:
            U = 'Poor Uniformity'

        print('Uniformity in this region is =', round(equity, 1), ',', U)
        # print("Equity for the given Raster is: ", equity)
        outLabel.setText('Uniformity in this region is = {}, {}   '.format(round(equity, 1), U))

    def beneficial_fraction(self, ta_dir, aeti_dir, output_name):
        """
        Beneficial fraction is computed from the formula:
        --- BF = (TA / AETI)
        --- Resolution: Continental, National, Sub-national 
        where:
            -- AETI - (raster) - Actual Evapotranspiration and Interception 
            --- Raster Types: AETI (annual, dekadal)
            --- Conversion Factor: 0.1
            -- TA - (raster) - Mean obtained from a Raster
                --- Raster Types: TA (annual, dekadal)
                --- Conversion Factor: 0.1
        --- Units: decimal or percentage(*100)

        Output:
        --- BF - Raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        ras_ta_dir = os.path.join(self.rasters_dir, ta_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)
        ras_ta = QgsRasterLayer(ras_ta_dir)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_ta
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('ras@2 / ras@1',
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())

    def adequacy(self, aeti_dir, output_name):
        """
        [FORMULA PASSED THE TEST WITH TRUE VALUES]
        Adequacy is computed from the formula:
        --- AD = (ETa / ETp)
        --- Resolution: Continental
        where:
            -- ETa - (raster) - Actual Evapotranspiration and Interception 
            --- Raster Types: AETI (annual, monthly, dekadal)
            -- ETp - (raster) - 95th percentile of AETI 
        --- Units: decimal or percentage(*100)

        Output:
        --- AD - Raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)

        ds = gdal.Open(ras_atei_dir)

        atei_band1 = self._get_array(ds)

        AETI1_1D  = np.reshape(atei_band1,  atei_band1.shape[0] * atei_band1.shape[1])

        ETp = np.nanpercentile(AETI1_1D, 99)
        # ETp_value = np.nanpercentile(atei_band1, 95)
        # ETp = np.full_like(atei_band1, ETp_value)
        # ETp  = np.reshape(ETp,  atei_band1.shape[0] * atei_band1.shape[1])

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('(ras@1) / {}'.format(ETp),
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())


    def relative_water_deficit(self, aeti_dir, output_name, outLabel):
        """
        [FORMULA PASSED THE TEST WITH TRUE VALUES]
        Relative water deficit is computed from the formula:
        --- RWD = 1 - (AETI / ETx)
        --- Resolution: Continental, National, Sub-national 
        where:
            -- AETI - (raster) - Actual Evapotranspiration and Interception 
            --- Raster Types: AETI (annual, monthly, dekadal)
            --- Conversion Factor: 0.1
            -- ETx - (real number) - 99 percentile of the actual evapotranspiration
        --- Formula: ETx = 99 percentile of a Raster (AETI)
                --- Raster Types: AETI (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
        --- Units: decimal or percentage(*100)

        Output:
        --- RWD - Raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)
        ras_atei = QgsRasterLayer(ras_atei_dir)

        ds = gdal.Open(ras_atei_dir)

        atei_band1 = self._get_array(ds)

        AETI1_1D  = np.reshape(atei_band1,  atei_band1.shape[0] * atei_band1.shape[1])
        ETx = np.nanpercentile(AETI1_1D, 95)

        AETI_mean = np.nanmean(atei_band1)

        RWD = 1 - (AETI_mean / ETx)
        outLabel.setText('Relative water deficit = {}'.format(round(RWD, 2)))

        print(ETx)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)
        
        calc = QgsRasterCalculator('1 - (ras@1 / {})'.format(str(ETx)),
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())



    def total_biomass_production(self, raster, output_name, outLabel):
        """
        TBP is computed from the formula:
            --- TBP = (NPP * 22.22)/1000
            where:
                -- NPP - Net Primary Production
                -- 22.222 is to convert the NPP in gC/m^2 to biomass production in kg/ha
                -- To convert to ton/ha the value is divided by 1000
        Output:
        --- mean & standard deviation - real number
        --- Total Biomass Production - raster
        """
        ras_npp_dir = os.path.join(self.rasters_dir, raster)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ds = gdal.Open(ras_npp_dir)
        ras_npp = QgsRasterLayer(ras_npp_dir)

        npp_band1 = self._get_array(ds)

        TBP = (npp_band1 * 22.222) / 1000

        TBPm   = np.nanmean(TBP)
        TBPsd  = np.nanstd(TBP)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_npp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('(ras@1 * 22.22) / 1000',
                                    output_dir,
                                    'GTiff',
                                    ras_npp.extent(),
                                    ras_npp.width(),
                                    ras_npp.height(),
                                    entries)
        print(calc.processCalculation())

        print('The mean and standard deviation for', raster, '=', round(TBPm, 2), ',', round(TBPsd, 2))
        outLabel.setText('mean = {}, \nstandard deviation = {}'.format(round(TBPm, 2), round(TBPsd, 2)))

    def biomass_water_productivity(self, aeti_dir, tbp_dir, output_name, outLabel):
        """
        WPb is computed from the formula:
            --- WPb = TBP/AETI * 100
            where:
                -- TBP - Total Biomass Production
                -- The multiplication with 100 is needed to correct the units, first convert TBP in ton/ha to kg/m^2 (divide by 10) and then AETI 
                -- from mm/season to m/season (divide by 1000) so that the final unit of WPb is kg/m^3
        Output:
        --- mean & standard deviation - real number
        --- Biomass Water Productivity - raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        ras_tbp_dir = os.path.join(self.rasters_dir, tbp_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)
        ras_tbp = QgsRasterLayer(ras_tbp_dir)

        ds_aeti = gdal.Open(ras_atei_dir)
        ds_tbp = gdal.Open(ras_tbp_dir)

        aeti_band = self._get_array(ds_aeti)
        tbp_band = self._get_array(ds_tbp)

        try:
            WP  = tbp_band/aeti_band*100
        except ValueError:
            outLabel.setText('Error: The two Rasters have different sizes!')
            return 0
        
        NPPm   = np.nanmean(WP)
        NPPsd  = np.nanstd(WP)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_tbp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('ras@2 / ras@1 * 100',
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())

        print('The mean and standard deviation for WP', '=', round(NPPm, 2), ',', round(NPPsd, 2))
        outLabel.setText('mean = {}, \nstandard deviation = {}'.format(round(NPPm, 2), round(NPPsd, 2)))

    def yield_indicator(self, raster, MC, fc, AOT, HI, output_name, outLabel):
        """
        Yield is computed with the formula: 
            --- Y = HI * AOT * fc * (TBP / (1 - MC))
            where:
                -- MC: moisture content, dry matter over fresh biomass
                -- fc: Light use efficiency correction factor
                -- AOT: above ground over total biomass production ratio (AOT) 
                -- HI: Harvest Index
                -- TBP - Total Biomass Production
        Output:
        --- mean & standard deviation - real number
        --- Yield - raster
        """
        ras_TBP_dir = os.path.join(self.rasters_dir, raster)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ds = gdal.Open(ras_TBP_dir)
        ras_npp = QgsRasterLayer(ras_TBP_dir)

        tbp_band1 = self._get_array(ds)

        YIELD = HI * AOT * fc * (tbp_band1 / (1 - MC))

        Yieldm   = np.nanmean(YIELD)
        Yieldsd  = np.nanstd(YIELD)

        entries = []
        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_npp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('{} * {} * {} * (ras@1 / (1 - {}))'.format(HI, AOT, fc, MC),
                                    output_dir,
                                    'GTiff',
                                    ras_npp.extent(),
                                    ras_npp.width(),
                                    ras_npp.height(),
                                    entries)
        print(calc.processCalculation())

        print('The mean and standard deviation for', raster, '=', round(Yieldm, 2), ',', round(Yieldsd, 2))
        outLabel.setText('mean = {}, \nstandard deviation = {}'.format(round(Yieldm, 2), round(Yieldsd, 2)))

    def crop_water_productivity(self, y_dir, aeti_dir, output_name, outLabel):
        """
        cWP is computed from the formula:
            --- cWP = Y/AETI * 100
            where:
                -- Y -  (raster) - Yield
                -- AETI - (raster) - Actual Evapotranspiration and Interception 
                -- The multiplication with 100 is to correct the units to kg/m3 (from AETI in mm/season and TBP in ton/ha) 
        Output:
        --- mean & standard deviation - real number
        --- Crop Water Productivity - raster
        """
        ras_y_dir = os.path.join(self.rasters_dir, y_dir)
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_y = QgsRasterLayer(ras_y_dir)
        ras_atei = QgsRasterLayer(ras_atei_dir)

        ds_y = gdal.Open(ras_y_dir)
        ds_aeti = gdal.Open(ras_atei_dir)

        y_band = self._get_array(ds_y)
        aeti_band = self._get_array(ds_aeti)

        try:
            cWP  = y_band/aeti_band*100
        except ValueError:
            outLabel.setText('Error: The two Rasters have different sizes!')
            return 0
        
        cWPm   = np.nanmean(cWP)
        cWPsd  = np.nanstd(cWP)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_y
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('ras@1 / ras@2 * 100',
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())

        print('The mean and standard deviation for cWP', '=', round(cWPm, 2), ',', round(cWPsd, 2))
        outLabel.setText('mean = {}, \nstandard deviation = {}'.format(round(cWPm, 2), round(cWPsd, 2)))

    def overall_consumed_ratio(self, aeti_dir, pcp_dir, output_name, V_ws):
        """
        Overall consumed ratio is computed from the formula:
        --- OCR = 1 - (AETI -PCP)/ V_ws
        --- Resolution: Continental
        where:
            -- AETI - (raster) - Actual Evapotranspiration and Interception 
                --- Raster Types: AETI (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- PCP - (raster) - Precipitation 
                --- Raster Types: PCP (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- V_ws - (real number) - Volume of water supplied to command area 
                --- User input -in mm (1mm=1l/m² or 1mm=10m³/ha) 

        Output:
            --- OCR - Raster

        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        ras_pcp_dir = os.path.join(self.rasters_dir, pcp_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)
        ras_pcp = QgsRasterLayer(ras_pcp_dir)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_pcp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('1.0 - (ras@1 - ras@2) / {}'.format(str(V_ws)),
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())

    def field_application_ratio(self, aeti_dir, pcp_dir, output_name, V_wd):
        """
        Field appliation ratio is computed from the formula:
        --- FAR = 1 - (AETI - PCP)/Vwd
        --- Resolution: Continental
        where:
            -- AETI - (raster) - Actual Evapotranspiration and Interception 
                --- Raster Types: AETI (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- PCP - (raster) - Precipitation 
                --- Raster Types: PCP (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- Vwd - (real number) - Volume of water delivered to field(s)
                --- User input -in mm (1mm=1l/m² or 1mm=10m³/ha) 

        --- Units: decimal or percentage(*100)

        Output:
        --- FAR - Raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        ras_pcp_dir = os.path.join(self.rasters_dir, pcp_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)
        ras_pcp = QgsRasterLayer(ras_pcp_dir)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_pcp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('1.0 - (ras@1 - ras@2) / {}'.format(str(V_wd)),
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())


    def depleted_fraction(self, aeti_dir, pcp_dir, output_name, V_c):
        """
        Depleted fraction is computed from the formula:
        --- DF = 1 - AETI /(PCP + Vc)
        --- Resolution: Continental
        where:
            -- AETI - (raster) - Actual Evapotranspiration and Interception 
                --- Raster Types: AETI (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- PCP - (raster) - Precipitation 
                --- Raster Types: PCP (annual, monthly, dekadal)
                --- Conversion Factor: 0.1
            -- Vc - (real number) - Volume of water consumed
                --- User input -in mm (1mm=1l/m² or 1mm=10m³/ha) 
        
        --- Units: decimal or percentage(*100)

        Output:
        --- DF - Raster
        """
        ras_atei_dir = os.path.join(self.rasters_dir, aeti_dir)
        ras_pcp_dir = os.path.join(self.rasters_dir, pcp_dir)
        output_dir = os.path.join(self.rasters_dir, output_name)

        ras_atei = QgsRasterLayer(ras_atei_dir)
        ras_pcp = QgsRasterLayer(ras_pcp_dir)

        entries = []

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@1'
        ras.raster = ras_atei
        ras.bandNumber = 1
        entries.append(ras)

        ras = QgsRasterCalculatorEntry()
        ras.ref = 'ras@2'
        ras.raster = ras_pcp
        ras.bandNumber = 1
        entries.append(ras)

        calc = QgsRasterCalculator('1.0 - ras@1/ (ras@2 + {})'.format(str(V_c)),
                                    output_dir,
                                    'GTiff',
                                    ras_atei.extent(),
                                    ras_atei.width(),
                                    ras_atei.height(),
                                    entries)
        print(calc.processCalculation())

    def _get_array(self, ds, nan_value=-9999):
        ras = ds.GetRasterBand(1).ReadAsArray()
        ras = ras.astype(np.float64)
        # Removing values that contain no data value 
        ras[ras < 0.0] = float('nan')
        return ras
    
    def crop_yield(self):
        raise NotImplementedError("Indicator: 'Crop Yield' not implemented yet.")
