"""
Experiment Simulator - Generate time-series well data
"""

import uuid
import numpy as np
from typing import Dict, List
from backend.data_loader import WellImageLoader


class ExperimentSimulator:
    """Simulate automated experiment with contamination over time"""
    
    def __init__(self, clean_dir: str = "1_Clean_Samples",
                 contaminated_dir: str = "2_Contaminated_Samples"):
        """
        Initialize simulator
        
        Args:
            clean_dir: Directory with clean images
            contaminated_dir: Directory with contaminated images
        """
        self.loader = WellImageLoader(clean_dir, contaminated_dir)
        self.experiments = {}  # Store active experiments
    
    def create_experiment(self, num_timepoints: int = 6,
                          interval_seconds: int = 10,
                          contamination_scenario: str = "gradual") -> str:
        """
        Create new experiment simulation
        
        Args:
            num_timepoints: Number of timepoints to generate
            interval_seconds: Time interval between measurements
            contamination_scenario: Scenario type
                - "gradual": Contamination appears gradually
                - "sudden": Contamination appears suddenly
                - "clean": All clean (control)
                - "random": Random contamination
                
        Returns:
            experiment_id
        """
        experiment_id = str(uuid.uuid4())
        
        # Generate timepoints
        timepoints = []
        for i in range(num_timepoints):
            time_seconds = i * interval_seconds
            wells_data = self._generate_wells_at_time(
                i, num_timepoints, contamination_scenario
            )
            
            timepoints.append({
                'time': time_seconds,
                'wells': wells_data
            })
        
        # Store experiment
        self.experiments[experiment_id] = {
            'experiment_id': experiment_id,
            'status': 'completed',  # Instant for demo
            'num_timepoints': num_timepoints,
            'interval_seconds': interval_seconds,
            'contamination_scenario': contamination_scenario,
            'timepoints': timepoints
        }
        
        return experiment_id
    
    def _generate_wells_at_time(self, timepoint_idx: int, 
                                total_timepoints: int,
                                scenario: str) -> List[Dict]:
        """
        Generate well data for specific timepoint
        
        Args:
            timepoint_idx: Current timepoint index (0-based)
            total_timepoints: Total number of timepoints
            scenario: Contamination scenario
            
        Returns:
            List of well data dictionaries
        """
        wells = []
        well_ids = ['A1', 'A2', 'A3']
        
        for well_id in well_ids:
            # Determine if this well should be contaminated at this time
            is_contaminated = self._should_be_contaminated(
                well_id, timepoint_idx, total_timepoints, scenario
            )
            
            # Get appropriate image
            if is_contaminated:
                # Choose contamination level based on time progression
                if timepoint_idx < total_timepoints // 3:
                    level = 'light'
                elif timepoint_idx < 2 * total_timepoints // 3:
                    level = 'medium'
                else:
                    level = 'heavy'
                
                image_path, image_array = self.loader.get_random_contaminated_image(level)
                true_label = 'contaminated'
            else:
                image_path, image_array = self.loader.get_random_clean_image()
                true_label = 'clean'
            
            wells.append({
                'well_id': well_id,
                'image_path': image_path,
                'image_array': image_array,
                'true_label': true_label
            })
        
        return wells
    
    def _should_be_contaminated(self, well_id: str, 
                                timepoint_idx: int,
                                total_timepoints: int,
                                scenario: str) -> bool:
        """Determine if well should be contaminated based on scenario"""
        
        if scenario == "clean":
            return False
        
        elif scenario == "gradual":
            # Custom progression:
            # t=0s (idx=0), 10s (idx=1), 20s (idx=2): すべてclean
            # t=30s (idx=3): A1のみcontaminated
            # t=40s (idx=4): A1のみcontaminated
            # t=50s (idx=5): A1とA2がcontaminated
            
            if well_id == "A1":
                return timepoint_idx >= 3  # Contaminated from t=30s (idx=3)
            elif well_id == "A2":
                return timepoint_idx >= 5  # Contaminated from t=50s (idx=5)
            elif well_id == "A3":
                return False  # Always clean
        
        elif scenario == "sudden":
            # A2 suddenly contaminated at timepoint 2
            if well_id == "A2":
                return timepoint_idx >= 2
            else:
                return False
        
        elif scenario == "random":
            # Random contamination with increasing probability
            prob = timepoint_idx / total_timepoints
            return np.random.random() < prob
        
        return False
    
    def get_experiment(self, experiment_id: str) -> Dict:
        """Get experiment data"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        return self.experiments[experiment_id]
    
    def get_well_image_path(self, experiment_id: str, 
                           time_seconds: int,
                           well_id: str) -> str:
        """Get image path for specific well at specific time"""
        experiment = self.get_experiment(experiment_id)
        
        # Find matching timepoint
        for tp in experiment['timepoints']:
            if tp['time'] == time_seconds:
                for well in tp['wells']:
                    if well['well_id'] == well_id:
                        return well['image_path']
        
        raise ValueError(f"Well {well_id} at time {time_seconds}s not found")

