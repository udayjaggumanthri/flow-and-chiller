THRESHOLDS = {
     "tvcv1": {
        "Temperature": {"minor":50.0},
        "XaxisRMSVelocity": {"minor":7},
        "YaxisRMSVelocity": {"minor":7},
        "ZaxisRMSVelocity": {"minor":7},
        # "XaxisHFRMSAcceleration": 2.5,
        # "YaxisHFRMSAcceleration": 2.5,
        # "ZaxisHFRMSAcceleration": 2.5,
        # "Magnitude": 5.5,
        # "R_Phase_line_Current": {"minor":750},
        # "Y_Phase_line_Current": {"minor":750},
        # "B_Phase_line_Current": {"minor":750},
        # "R_Phase_line_Current": {
        #     "minor": 1200,
        # },
        # "Y_Phase_line_Current": {
        #     "minor": 1200,
        # },
        # "B_Phase_line_Current": {
        #     "minor": 1200,
        # },
        # "avg_Current": {
        #     "minor": 1200,
        # },
        "RY_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "YB_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "BR_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "RN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "BN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "YN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        # "avg_Voltage": {
        #     "minor": (390, 430),

        # },
        # "Rph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Yph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Bph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "avg_Power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Frequency": {
        #     "minor": (49.91, 50.00),
        # },
        # "Total_KW_wrt_line": {
        #     "minor": 850.0,
        # }
    },
    # 800TR chiller
    "tvcv3": {
        "Temperature": {"minor":50.0},
        "XaxisRMSVelocity": {"minor":7},
        "YaxisRMSVelocity": {"minor":7},
        "ZaxisRMSVelocity": {"minor":7},
        # "XaxisHFRMSAcceleration": 2.5,
        # "YaxisHFRMSAcceleration": 2.5,
        # "ZaxisHFRMSAcceleration": 2.5,
        # "Magnitude": 5.5,
        # "R_Phase_line_Current": {"minor":750},
        # "Y_Phase_line_Current": {"minor":750},
        # "B_Phase_line_Current": {"minor":750},
        # "avg_Current": {"minor":750},
        "RY_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "YB_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "BR_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "RN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "BN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "YN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        # "avg_Voltage": {"minor":(207, 230)},  # 253
    
        # "Rph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Yph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Bph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "avg_Power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Frequency": {
        #     "minor": (49.91, 50.00),
        # },
        # "Total_KW_wrt_line": {"minor":550},
    },
    "tvcv4": {
        "Temperature": {"minor":50.0},
        "XaxisRMSVelocity": {"minor":7},
        "YaxisRMSVelocity": {"minor":7},
        "ZaxisRMSVelocity": {"minor":7},
        # "XaxisHFRMSAcceleration": 2.5,
        # "YaxisHFRMSAcceleration": 2.5,
        # "ZaxisHFRMSAcceleration": 2.5,
        # "Magnitude": 5.5,
        # "R_Phase_line_Current": {"minor":750},
        # "Y_Phase_line_Current": {"minor":750},
        # "B_Phase_line_Current": {"minor":750},
        "R_Phase_line_Current": {"minor":750},
        "Y_Phase_line_Current": {"minor":750},
        "B_Phase_line_Current": {"minor":750},
        "avg_Current": {"minor":750},
        "RY_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "YB_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "BR_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "RN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "BN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "YN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "avg_Voltage": {"minor":(207, 230)},  # 253
    
        "Rph_power_Factor": {
            "minor": (0.7, 1.0),
        },
        "Yph_power_Factor": {
            "minor": (0.7, 1.0),
        },
        "Bph_power_Factor": {
            "minor": (0.7, 1.0),
        },
        "avg_Power_Factor": {
            "minor": (0.7, 1.0),
        },
        "Frequency": {
            "minor": (49.91, 50.00),
        },
        "Total_KW_wrt_line": {"minor":550},
    },
    "tvcv5": {
         "Temperature": {"minor":50.0},
        "XaxisRMSVelocity": {"minor":7},
        "YaxisRMSVelocity": {"minor":7},
        "ZaxisRMSVelocity": {"minor":7},
        # "XaxisHFRMSAcceleration": 2.5,
        # "YaxisHFRMSAcceleration": 2.5,
        # "ZaxisHFRMSAcceleration": 2.5,
        # "Magnitude": 5.5,
        # "R_Phase_line_Current": {"minor":750},
        # "Y_Phase_line_Current": {"minor":750},
        # "B_Phase_line_Current": {"minor":750},
        # "R_Phase_line_Current": {"minor":750},
        # "Y_Phase_line_Current": {"minor":750},
        # "B_Phase_line_Current": {"minor":750},
        # "avg_Current": {"minor":750},
        "RY_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "YB_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "BR_Voltage": {
            "minor": (430),
            "major": (440),
        },
        "RN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "BN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        "YN_Voltage": {
            # "minor": 240.0,
            "major": 245.0,
            "critical": 250.0
        },
        # "avg_Voltage": {"minor":(207, 230)},  # 253
    
        # "Rph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Yph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Bph_power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "avg_Power_Factor": {
        #     "minor": (0.7, 1.0),
        # },
        # "Frequency": {
        #     "minor": (49.91, 50.00),
        # },
        # "Total_KW_wrt_line": {"minor":550},
    },
    # Duplicate tvcv1 and assign to tvcv6
}
THRESHOLDS["tvcv2"] = {**THRESHOLDS["tvcv1"]}
