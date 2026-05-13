from typing import Dict, Any, List, Tuple
from .models import NodeObject, EdgeObject

class LayoutEngine:
    def __init__(self, nodes: Dict[str, NodeObject], edges: List[EdgeObject]):
        self.nodes = nodes
        self.edges = edges
        self.vertical_spacing = 60
        self.horizontal_spacing = 40
        self.start_x = 400
        self.start_y = 100

    def get_dimensions(self, text: str, node_type: int) -> Tuple[float, float]:
        lines = text.split('\n')
        max_len = max(len(line) for line in lines) if lines else 0
        
        # Эвристика ширины: ~7.5 пикселей на символ плюс отступы
        width = max(140.0, float(max_len * 7.5 + 40))
        
        # Условия и циклы требуют чуть больше пространства по горизонтали из-за скошенных краев
        if node_type == 2:  # Ромб
            width *= 1.4
        elif node_type == 6:  # Шестиугольник
            width *= 1.2
            
        height = max(60.0, float(len(lines) * 20 + 30))
        if node_type == 2:
            height *= 1.2 
            
        return width, height

    def calculate_positions(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict]]:
        layers: Dict[int, list] = {}
        # Сначала просто собираем слои и размеры
        dummy_index = 0
        
        for n_id, n in self.nodes.items():
            if n.layer not in layers:
                layers[n.layer] = []
            
            w, h = self.get_dimensions(n.text, n.type)
            layers[n.layer].append({
                "id": n_id, "node": n, "is_dummy": False, 
                "width": w, "height": h, "order": n.order
            })
            
        positions = {}
        max_heights_per_layer = {}
        
        # 2. Сортируем узлы в слоях
        for layer_idx in sorted(layers.keys()):
            items = layers[layer_idx]
            with_order = [it for it in items if it["order"] is not None]
            without_order = [it for it in items if it["order"] is None]
            
            with_order.sort(key=lambda x: x["order"])
            cur_order = with_order[-1]["order"] + 1 if with_order else 0
            
            for it in without_order:
                it["order"] = cur_order
                cur_order += 1
                with_order.append(it)
                
            with_order.sort(key=lambda x: x["order"])
            layers[layer_idx] = with_order
            
            max_h = max(it["height"] for it in with_order) if with_order else 60
            max_heights_per_layer[layer_idx] = max_h
            
        # 3. Рассчитываем физические координаты Y
        current_y = self.start_y
        layer_y_coords = {}
        for layer_idx in sorted(layers.keys()):
            # Выравниваем все блоки в слое по середине максимальной высоты блока этого слоя
            layer_y_coords[layer_idx] = current_y + (max_heights_per_layer.get(layer_idx, 60) / 2)
            current_y += max_heights_per_layer.get(layer_idx, 60) + self.vertical_spacing

        # 4. Рассчитываем физические координаты X
        for layer_idx, items in layers.items():
            total_width = sum(it["width"] for it in items) + (len(items) - 1) * self.horizontal_spacing
            
            # Start X выравнивается так, чтобы весь слой был по центру относительно self.start_x
            current_left_x = self.start_x - (total_width / 2)
            
            for it in items:
                # X верхнего левого угла для drawio
                it["x"] = current_left_x
                # Переводим Y верхнего левого края исходя из индивидуальной высоты блока
                it["y"] = layer_y_coords[layer_idx] - (it["height"] / 2)
                
                if not it["is_dummy"]:
                    positions[it["id"]] = {
                        "x": it["x"],
                        "y": it["y"],
                        "width": it["width"],
                        "height": it["height"]
                    }
                else:
                    # Для фиктивного узла нам понадобится центральная точка
                    positions[it["id"]] = {
                        "cx": it["x"] + it["width"]/2,
                        "cy": layer_y_coords[layer_idx]
                    }
                
                current_left_x += it["width"] + self.horizontal_spacing
                
        # 5. Сборка маршрутов для соединений по новой логике
        final_edges = []
        
        # Найдем абсолютные X-границы схемы для огибания
        max_right_x = max(p["x"] + p["width"] for p in positions.values()) if positions else 0
        min_left_x = min(p["x"] for p in positions.values()) if positions else 0
        
        for edge in self.edges:
            waypoints = []
            u_node = self.nodes.get(edge.from_node)
            v_node = self.nodes.get(edge.to_node)
            
            if not u_node or not v_node:
                final_edges.append({"from": edge.from_node, "to": edge.to_node, "label": edge.label, "waypoints": [], "style_attrs": ""})
                continue
                
            u_layer = u_node.layer
            v_layer = v_node.layer
            u_pos = positions.get(edge.from_node)
            v_pos = positions.get(edge.to_node)
            
            style_attrs = ""
            if v_layer <= u_layer:
                # Обратная связь (цикл). Пускаем справа от схемы
                style_attrs = "entryX=1;entryY=0.5;exitX=1;exitY=0.5;"
                side_x = max_right_x + 60
                waypoints = [
                    {"x": side_x, "y": u_pos["y"] + u_pos["height"]/2},
                    {"x": side_x, "y": v_pos["y"] + v_pos["height"]/2}
                ]
            else:
                style_attrs = "entryX=0.5;entryY=0;exitX=0.5;exitY=1;"
                # Прямая связь
                if v_layer > u_layer + 1:
                    # Прыжок через слои, проверяем пересечения с хитбоксами
                    pad = 15
                    u_c = u_pos["x"] + u_pos["width"] / 2
                    v_c = v_pos["x"] + v_pos["width"] / 2
                    
                    # Генерируем возможные варианты X координат для прохода (вертикальные "коридоры")
                    candidates = [u_c, v_c, min_left_x - pad - 30, max_right_x + pad + 30]
                    for l in range(u_layer + 1, v_layer):
                        for item in layers.get(l, []):
                            candidates.append(item["x"] - pad)
                            candidates.append(item["x"] + item["width"] + pad)
                            
                    # Отфильтруем те, которые пересекают блоки
                    safe_candidates = []
                    for cx in candidates:
                        is_safe = True
                        for l in range(u_layer + 1, v_layer):
                            for item in layers.get(l, []):
                                if (item["x"] - pad) < cx < (item["x"] + item["width"] + pad):
                                    is_safe = False
                                    break
                            if not is_safe:
                                break
                        if is_safe:
                            safe_candidates.append(cx)
                            
                    if safe_candidates:
                        # Сортируем: чем ближе к прямой линии между u и v, тем лучше
                        best_x = min(safe_candidates, key=lambda x: abs(x - u_c) + abs(x - v_c))
                        
                        # Если best_x не совпадает с u_c/v_c, расставляем путевые точки, 
                        # чтобы DrawIO не импровизировал и ровно прошел через коридор best_x
                        if abs(best_x - u_c) > 5 or abs(best_x - v_c) > 5:
                            waypoints = [
                                {"x": best_x, "y": u_pos["y"] + u_pos["height"] + self.vertical_spacing / 2.0},
                                {"x": best_x, "y": v_pos["y"] - self.vertical_spacing / 2.0}
                            ]
                
            final_edges.append({
                "from": edge.from_node,
                "to": edge.to_node,
                "label": edge.label,
                "waypoints": waypoints,
                "style_attrs": style_attrs
            })
        
        return positions, final_edges
