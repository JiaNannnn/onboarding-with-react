import json
import csv
import os
from typing import List, Dict, Any, Optional
import logging
import random
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMGrouper:
    """Handles grouping and mapping BMS points using a simulated LLM API."""

    def __init__(self, chunk_size: int = 100, enos_template_path: str = 'enos_simlified.json'):
        """
        Args:
            chunk_size: Number of point names to send to the LLM for grouping.
            enos_template_path: Path to the EnOS simplified template JSON file.
        """
        self.chunk_size = chunk_size
        self.enos_template = self._load_enos_template(enos_template_path)
        # TODO: Replace this with actual client initialization for the LLM API (e.g., OpenAI client)
        # self.llm_client = initialize_llm_client()

    def _load_enos_template(self, file_path: str) -> Dict[str, Any]:
        """Loads the EnOS template JSON file."""
        # Construct path relative to this file's directory if needed
        if not os.path.isabs(file_path):
            current_dir = os.path.dirname(__file__)
            # Assuming enos_simlified.json is in the parent 'backend' directory
            parent_dir = os.path.dirname(current_dir) 
            full_path = os.path.join(parent_dir, file_path)
        else:
            full_path = file_path
            
        if not os.path.exists(full_path):
            logger.error(f"EnOS template file not found at path: {full_path}")
            raise FileNotFoundError(f"EnOS template file not found: {full_path}")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            logger.info(f"Successfully loaded EnOS template from {full_path}")
            return template
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from EnOS template {full_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading EnOS template file {full_path}: {e}")
            raise

    def _read_point_names_from_csv(self, file_path: str, point_name_column: str = "pointName") -> List[str]:
        """Reads point names from a specific column in a CSV file."""
        point_names = []
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found at path: {file_path}")
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if point_name_column not in reader.fieldnames:
                    logger.error(f"Column '{point_name_column}' not found in CSV header: {reader.fieldnames}")
                    raise ValueError(f"Column '{point_name_column}' not found in CSV header.")
                
                for row in reader:
                    if row.get(point_name_column):
                        point_names.append(row[point_name_column])
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise

        logger.info(f"Read {len(point_names)} point names from {file_path}")
        return point_names

    def _chunk_list(self, data: List[Any], size: int) -> List[List[Any]]:
        """Splits a list into chunks of a specified size."""
        return [data[i:i + size] for i in range(0, len(data), size)]

    def _build_llm_grouping_prompt(self, point_names_chunk: List[str]) -> str:
        """Builds the prompt for the LLM API for grouping."""
        prompt = (
            "Group the following list of building automation system point names by system and component instance. "
            "Identify the main system (e.g., CH-SYS-1, FCU, DPM) and the specific component instance "
            "(e.g., CH, CHWP, CWP, FCU_01_25, CH_1). Return the result as structured JSON. "
            "Ignore entries that seem like general system views (e.g., 'ChillerPlant', 'Fcu') or driver points "
            "unless they clearly map to a component. Ensure the output is ONLY the JSON object, with no extra text.\n\n"
            "Point Names:\n"
            f"{json.dumps(point_names_chunk, indent=2)}"
        )
        return prompt

    def _call_llm_api_grouping_simulated(self, prompt: str, point_names_chunk: List[str]) -> Dict[str, Any]:
        """
        Simulates a call to an LLM API (e.g., GPT-4o) for GROUPING.
        *** THIS IS A PLACEHOLDER/SIMULATION ***
        """
        logger.warning("Using SIMULATED LLM API call for GROUPING. Replace with actual implementation.")
        
        # --- Simulation Logic (Improved Fallback) ---
        simulated_groups = {}
        
        for point_name in point_names_chunk:
            matched_system_key = None
            component_instance_key = None
            found = False

            # Ignore simple views
            if point_name in ["ChillerPlant", "Fcu"]: continue
            # Ignore simple driver points (basic check)
            if point_name.lower().startswith("driver"):
                # Could potentially try to map driver points later if needed
                continue 

            # 1. Try CH-SYS style: CH-SYS-X.COMPONENT.*
            sys_match = re.match(r"^(CH-SYS-\d+)\.([A-Za-z]+(?:-\d+)?)(?:\.|$)", point_name)
            if sys_match:
                matched_system_key = sys_match.group(1) # e.g., CH-SYS-1
                component_instance_key = sys_match.group(2) # e.g., CH, CHWP, CWP, ATCS
                found = True

            # 2. Try FCU style: FCU_XX_YY... or FCU.FCU_XX...
            if not found:
                fcu_match = re.match(r"^(?:FCU\.)?(FCU_\d+(?:[_.]\d+)*)(?:\.|_|$)", point_name, re.IGNORECASE)
                if fcu_match:
                    matched_system_key = "FCU"
                    component_instance_key = fcu_match.group(1) # e.g., FCU_01_25, FCU_01_26.27_1
                    # Normalize key slightly for consistency?
                    component_instance_key = component_instance_key.replace(".", "_") 
                    found = True

            # 3. Try DPM style: DPM_COMPONENT_ID.*
            if not found:
                 dpm_match = re.match(r"^(DPM_([A-Za-z]+)_\d+)(?:\.|$)", point_name, re.IGNORECASE)
                 if dpm_match:
                     matched_system_key = "DPM"
                     component_instance_key = dpm_match.group(1) # e.g., DPM_CH_1
                     found = True

            # 4. Fallback: Simple prefix match (e.g., any CH-SYS-*, DPM_*, FCU_*)
            if not found:
                for prefix in ["CH-SYS", "FCU", "DPM"]:
                    if point_name.upper().startswith(prefix):
                         matched_system_key = prefix
                         # Use the first part as instance key as a crude fallback
                         component_instance_key = point_name.split('.')[0].split('_')[0]
                         logger.debug(f"Fallback grouping for {point_name} under {matched_system_key}.{component_instance_key}")
                         found = True
                         break # Take first prefix match
                         
            # Add to groups if found
            if found and matched_system_key and component_instance_key:
                 if matched_system_key not in simulated_groups:
                     simulated_groups[matched_system_key] = {}
                 if component_instance_key not in simulated_groups[matched_system_key]:
                     simulated_groups[matched_system_key][component_instance_key] = []
                 simulated_groups[matched_system_key][component_instance_key].append(point_name)
            elif not found:
                 logger.debug(f"Point ignored by grouping simulation: {point_name}")

        # Simulate API errors (remains same)
        if random.random() < 0.05: 
             logger.error("Simulating LLM GROUPING API error (e.g., invalid JSON).")
             return {"error": "Simulated Grouping API error"}
             
        return simulated_groups

    def _merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merges grouping results from multiple LLM calls (chunks)."""
        merged = {}
        errors = []

        for result_chunk in results:
            if not isinstance(result_chunk, dict):
                errors.append({"error": "Invalid result format received", "chunk_data": result_chunk})
                continue
            if "error" in result_chunk:
                 errors.append(result_chunk) # Log errors from API calls
                 continue

            for system, components in result_chunk.items():
                # Skip internal error reporting key
                if system == "_errors": continue 
                
                if not isinstance(components, dict):
                     errors.append({"error": f"Expected dict for system '{system}', got {type(components)}", "chunk_data": result_chunk})
                     continue
                 
                if system not in merged:
                    merged[system] = {}

                for instance, points in components.items():
                    if not isinstance(points, list):
                         errors.append({"error": f"Expected list for instance '{system}.{instance}', got {type(points)}", "chunk_data": result_chunk})
                         continue
                         
                    if instance not in merged[system]:
                        merged[system][instance] = {"points": []} # Store points under a key
                    
                    # Avoid duplicate points if chunking logic overlaps somehow
                    for point in points:
                         if point not in merged[system][instance]["points"]:
                             merged[system][instance]["points"].append(point)

        # Optionally include errors in the final output or handle them separately
        if errors:
            # Avoid overwriting if merging multiple error lists
            if "_errors" not in merged:
                 merged["_errors"] = []
            merged["_errors"].extend(errors)
            logger.warning(f"Encountered {len(errors)} errors during LLM processing.")

        return merged

    def _get_equipment_type_from_key(self, system_key: str, instance_key: str) -> Optional[str]:
        """Infers the general equipment type (e.g., Chiller, FCU) from group keys."""
        # Simple heuristic - could be improved or use another LLM call if needed
        if system_key == "FCU":
            return "Fan Coil Unit"
        elif system_key == "DPM":
             # Try to find what the DPM is measuring (CH, CHWP, etc.)
             parts = instance_key.split('_') # DPM_CH_1 -> [DPM, CH, 1]
             if len(parts) > 1:
                  type_guess = parts[1]
                  # Find full name from short name in template
                  for name, data in self.enos_template.items():
                       if data.get("shortName") == type_guess:
                            logger.info(f"Inferred DPM is measuring: {name}")
                            # For mapping purposes, maybe treat DPM points based on what they measure?
                            # Or define a specific DPM template in enos_simlified.json?
                            # Returning None for now to indicate no direct equipment template
                            return None 
             return None # No specific equipment type for a generic DPM
        elif system_key.startswith("CH-SYS"):
            component_short_name = instance_key.split('.')[0] # CH, CHWP, CWP
            for name, data in self.enos_template.items():
                if data.get("shortName") == component_short_name:
                    return name
        
        # Fallback: Check if instance key matches a short name directly
        for name, data in self.enos_template.items():
            if data.get("shortName") == instance_key:
                 return name
                 
        logger.warning(f"Could not determine equipment type for: {system_key}.{instance_key}")
        return None

    def _build_llm_mapping_prompt(self, equipment_type_name: str, enos_template_points: List[str], bms_points: List[str]) -> str:
        """Builds the prompt for the LLM API for mapping."""
        prompt = (
            f"MAP the given BMS points for a '{equipment_type_name}' component to the standard EnOS points listed below. "
            "Return the result as a structured JSON object where keys are the BMS point names and values are the corresponding EnOS point names. "
            "If a BMS point does not have a clear match in the EnOS list, map it to null or omit it. "
            "Ensure the output is ONLY the JSON object, with no extra text.\n\n"
            f"EnOS Points for {equipment_type_name}:\n"
            f"{json.dumps(enos_template_points, indent=2)}\n\n"
            "BMS Points to Map:\n"
            f"{json.dumps(bms_points, indent=2)}"
        )
        return prompt

    def _call_llm_mapping_simulated(self, prompt: str, bms_points: List[str], enos_points: List[str]) -> Dict[str, Optional[str]]:
        """
        Simulates a call to an LLM API (e.g., GPT-4o) for MAPPING.
        *** THIS IS A PLACEHOLDER/SIMULATION ***
        """
        logger.warning("Using SIMULATED LLM API call for MAPPING. Replace with actual implementation.")
        
        # --- Simulation Logic ---
        # Very basic simulation: attempts simple keyword matching.
        simulated_mapping = {}
        enos_keywords = {pt: set(re.findall(r'[a-zA-Z]+', pt.split('_')[-1])) for pt in enos_points} # Extract keywords like 'status', 'temp'

        for bms_pt in bms_points:
            bms_keywords = set(re.findall(r'[a-zA-Z]+', bms_pt.split('.')[-1])) # Keywords from last part
            best_match = None
            max_overlap = 0

            for enos_pt, enos_kws in enos_keywords.items():
                overlap = len(bms_keywords.intersection(enos_kws))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_match = enos_pt
            
            # Only map if there's at least one keyword overlap
            simulated_mapping[bms_pt] = best_match if max_overlap > 0 else None

        if random.random() < 0.05:
            logger.error("Simulating LLM MAPPING API error.")
            # Return an error structure or simulate bad JSON
            return {"error": "Simulated Mapping API error"} 
            
        return simulated_mapping
        # --- End Simulation Logic ---

        # --- Replace with actual API call (similar to grouping) ---
        # try: 
        #     response = self.llm_client.chat.completions.create(...) 
        #     content = ...
        #     parsed_json = json.loads(content)
        #     return parsed_json
        # except ... : 
        #     return {"error": ...}
        # --- End Actual Call --- 

    def group_and_map_points_from_csv(self, file_path: str, point_name_column: str = "pointName") -> Dict[str, Any]:
        """
        Reads points, groups them using LLM (simulated), and then maps each group using LLM (simulated).
        """
        logger.info(f"Starting group and map process for file: {file_path}")
        # 1. Read Points
        try:
            point_names = self._read_point_names_from_csv(file_path, point_name_column)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to read points: {e}")
            return {"error": str(e)}
        if not point_names:
            logger.warning("No point names found in the CSV file.")
            return {"error": "No point names found in the CSV file."}
        logger.debug(f"Read {len(point_names)} point names. First few: {point_names[:5]}")

        # 2. Group Points via LLM (Chunked)
        point_chunks = self._chunk_list(point_names, self.chunk_size)
        logger.info(f"Split points into {len(point_chunks)} chunks of size {self.chunk_size} for grouping.")
        grouping_results = []
        for i, chunk in enumerate(point_chunks):
            logger.info(f"Processing grouping chunk {i+1}/{len(point_chunks)}...")
            prompt = self._build_llm_grouping_prompt(chunk)
            logger.debug(f"Grouping Prompt (first 100 chars): {prompt[:100]}...")
            result = self._call_llm_api_grouping_simulated(prompt, chunk) 
            logger.debug(f"Grouping Result (chunk {i+1}): {json.dumps(result, indent=2)}")
            grouping_results.append(result)
        
        logger.info("Merging grouping results...")
        grouped_data = self._merge_results(grouping_results)
        logger.debug(f"Merged Grouping Data: {json.dumps(grouped_data, indent=2)}")
        
        # Check for grouping errors before proceeding
        if "_errors" in grouped_data:
             logger.warning("Errors occurred during the grouping phase. Mapping might be incomplete.")
             # Decide whether to stop or continue. Continuing for now.

        # 3. Map Points within each Group via LLM
        logger.info("Starting mapping phase...")
        mapping_errors = []
        final_output = grouped_data # Start with the grouped structure
        
        for system_key, components in grouped_data.items():
             if system_key == "_errors": continue # Skip error reporting key
             if not isinstance(components, dict):
                  logger.warning(f"Skipping malformed system data for key '{system_key}'")
                  continue # Skip malformed data
                 
             logger.debug(f"Processing system: {system_key}")
             for instance_key, instance_data in components.items():
                  logger.debug(f"Processing instance: {instance_key}")
                  if not isinstance(instance_data, dict) or "points" not in instance_data:
                       logger.warning(f"Skipping malformed instance data for key '{system_key}.{instance_key}'")
                       continue # Skip malformed instance data
                       
                  bms_points_in_group = instance_data["points"]
                  if not bms_points_in_group:
                       logger.debug(f"Skipping empty group: {system_key}.{instance_key}")
                       continue
                       
                  # Determine equipment type for EnOS template selection
                  equipment_type = self._get_equipment_type_from_key(system_key, instance_key)
                  logger.debug(f"Inferred equipment type for {system_key}.{instance_key}: {equipment_type}")
                  
                  if equipment_type and equipment_type in self.enos_template:
                       enos_points_for_type = self.enos_template[equipment_type].get("points", [])
                       if not enos_points_for_type:
                            logger.warning(f"No EnOS points found in template for type: {equipment_type}")
                            instance_data["mapping"] = {"error": f"No EnOS points in template for {equipment_type}"}
                            continue
                            
                       logger.info(f"Mapping {len(bms_points_in_group)} points for {system_key}.{instance_key} (Type: {equipment_type}) using {len(enos_points_for_type)} EnOS points.")
                       mapping_prompt = self._build_llm_mapping_prompt(equipment_type, enos_points_for_type, bms_points_in_group)
                       logger.debug(f"Mapping Prompt (first 100 chars): {mapping_prompt[:100]}...")
                       mapping_result = self._call_llm_mapping_simulated(mapping_prompt, bms_points_in_group, enos_points_for_type)
                       logger.debug(f"Mapping Result for {system_key}.{instance_key}: {json.dumps(mapping_result, indent=2)}")
                       
                       # Store mapping result, including potential errors from the API call
                       instance_data["mapping"] = mapping_result 
                       if isinstance(mapping_result, dict) and "error" in mapping_result:
                            mapping_errors.append({
                                 "group": f"{system_key}.{instance_key}", 
                                 "error_details": mapping_result
                            })
                  else:
                       logger.warning(f"Skipping mapping for {system_key}.{instance_key}: Could not determine equipment type or find template.")
                       instance_data["mapping"] = {"error": f"Could not find matching EnOS template for inferred type '{equipment_type}'"}

        # Add mapping errors to the final output if any occurred
        if mapping_errors:
             if "_errors" not in final_output:
                  final_output["_errors"] = []
             final_output["_errors"].append({"phase": "mapping", "details": mapping_errors})
             logger.warning(f"Encountered {len(mapping_errors)} errors during the mapping phase.")
             
        logger.info("Grouping and mapping process complete.")
        logger.debug(f"Final Output Data: {json.dumps(final_output, indent=2)}") # Log final output before returning
        return final_output

# Example usage remains the same, but calls the combined function
if __name__ == '__main__':
    # Restore original main block, removing path hacks and extra prints
    import logging
    import json
    import os
    
    # Basic logging config (should work when run via -m)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("--- Starting LLM Grouper via -m ---")

    # Relative paths should be okay when run from backend dir via -m
    csv_path = 'data_test/points_5xkIipSH_10102_192.168.10.102_47808_20250312_173540.csv'
    enos_path = 'enos_simlified.json' 
    
    try:
        # Need to import within main when run as script/module
        from app.bms.llm_grouper import LLMGrouper
        
        grouper = LLMGrouper(chunk_size=70, enos_template_path=enos_path) 
        
        processed_data = grouper.group_and_map_points_from_csv(csv_path)
        
        print("--- Final Processed Data ---")
        print(json.dumps(processed_data, indent=2))
    
        if "_errors" in processed_data:
            print("\n--- Errors Encountered ---")
            for error_item in processed_data["_errors"]:
                print(json.dumps(error_item, indent=2)) 
                
    except FileNotFoundError as fnf:
         logger.error(f"File Not Found: {fnf}")
         print(f"SCRIPT FAILED: File Not Found - {fnf}")
    except Exception as e:
        logger.error("Unhandled exception during script execution:", exc_info=True)
        print(f"SCRIPT FAILED: {type(e).__name__} - {e}")
        
    logger.info("--- LLM Grouper Script Execution Complete ---") 