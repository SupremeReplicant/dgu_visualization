reference_limits = {
    1: 87,
    2: 51,
    3: 60,
    '4-15': 450,
    '16-27': 100,
    28: 80,
    29: 80
}

def check_temperatures(temps):
    results = {}
    for i in [1, 2, 3, 28, 29]:
        results[i] = temps[i-1] <= reference_limits[i]
    
    segment_4_15 = temps[3:15]
    results['4-15_individual'] = []
    
    if len(segment_4_15) > 0:
        for temp in segment_4_15:
            results['4-15_individual'].append(temp <= reference_limits['4-15'])

        min_temp = min(segment_4_15)
        max_temp = max(segment_4_15)
        mean_4_15 = sum(segment_4_15) / len(segment_4_15)
        results['4-15_spread'] = ((max_temp - min_temp) / mean_4_15) * 100 if mean_4_15 != 0 else 0
    else:
        results['4-15_spread'] = 0
        mean_4_15 = 0
    
    segment_16_27 = temps[15:27]
    results['16-27_individual'] = []
    
    if len(segment_16_27) > 0:
        for temp in segment_16_27:
            results['16-27_individual'].append(temp <= reference_limits['16-27'])
    else:
        pass
    
    return results, mean_4_15

def create_comparison_table(temps, check_results, part_names):
    table_data = []
    for i in range(29):
        if i < len(temps):
            temp_value = temps[i]
        else:
            temp_value = 0
            
        if 4 <= i+1 <= 15:
            etalon = reference_limits['4-15']
            group_index = i - 3  
            if group_index < len(check_results.get('4-15_individual', [])):
                result = check_results['4-15_individual'][group_index]
            else:
                result = True
                
        elif 16 <= i+1 <= 27:
            etalon = reference_limits['16-27']
            group_index = i - 15  
            if group_index < len(check_results.get('16-27_individual', [])):
                result = check_results['16-27_individual'][group_index]
            else:
                result = True
                
        else:
            etalon = reference_limits.get(i+1, '-')
            result = check_results.get(i+1, True)

        if i < len(part_names):
            part_name = part_names[i]
        else:
            part_name = f"Деталь {i+1}"

        table_data.append({
            'Номер': i+1,
            'Деталь': part_name,
            'Введенная температура': temp_value,
            'Эталонная температура': etalon,
            'Комментарий': 'Отклонений нет' if result else 'Температура превышает норму'
        })
    return table_data