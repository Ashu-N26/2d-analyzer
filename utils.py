import numpy as np

def generate_approach_profile(faf_distance, faf_altitude, threshold_altitude, sdf_data):
    """
    Generates descent profile from FAF to threshold with optional step-down fixes.
    """
    # Start with FAF and threshold
    profile_points = [(faf_distance, faf_altitude)] + sdf_data + [(0, threshold_altitude)]
    profile_points.sort(reverse=True)

    distances = []
    alts = []
    for i in range(len(profile_points)-1):
        start_nm, start_alt = profile_points[i]
        end_nm, end_alt = profile_points[i+1]
        segment_d = int((start_nm - end_nm) * 10) + 1  # finer resolution
        seg_x = np.linspace(start_nm, end_nm, segment_d)
        seg_y = np.linspace(start_alt, end_alt, segment_d)
        distances.extend(seg_x)
        alts.extend(seg_y)

    return distances, alts
