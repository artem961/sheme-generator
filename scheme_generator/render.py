import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any
from .models import SchemeSchema

class DrawioRenderer:
    def __init__(self, schema: SchemeSchema, positions: Dict[str, Dict[str, Any]], final_edges: List[Dict]):
        self.schema = schema
        self.positions = positions
        self.final_edges = final_edges

    def _get_style_for_type(self, node_type: int) -> str:
        styles = {
            1: "rounded=0;whiteSpace=wrap;html=1;", # Действие (Прямоугольник)
            2: "rhombus;whiteSpace=wrap;html=1;", # Условие (Ромб)
            3: "shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;", # Вызов функции
            4: "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;", # Данные (Ввод/Вывод)
            5: "ellipse;whiteSpace=wrap;html=1;", # Начало / Конец
            6: "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;" # Цикл
        }
        return styles.get(node_type, "rounded=0;whiteSpace=wrap;html=1;")

    def render(self) -> str:
        mxfile = ET.Element("mxfile", version="26.0.0")
        diagram = ET.SubElement(mxfile, "diagram", id="scheme-gen", name=self.schema.meta.get("name", "Page-1"))
        model = ET.SubElement(diagram, "mxGraphModel", dx="1000", dy="1000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="827", pageHeight="1169", math="0", shadow="0")
        root = ET.SubElement(model, "root")

        # Базовые слои draw.io
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        # Добавляем узлы
        for node_id, node in self.schema.nodes.items():
            pos = self.positions.get(node_id, {"x": 0, "y": 0, "width": 120, "height": 60})
            
            # Заменяем переносы строк на <br> для HTML отображения
            formatted_text = node.formatted_text.replace('\n', '<br>')
            
            cell = ET.SubElement(root, "mxCell", id=node_id, value=formatted_text, style=self._get_style_for_type(node.type), vertex="1", parent="1")
            
            geom = ET.SubElement(cell, "mxGeometry", x=str(pos["x"]), y=str(pos["y"]), width=str(pos["width"]), height=str(pos["height"]))
            geom.set("as", "geometry")

        # Добавляем связи (сортируем для предсказуемости)
        for i, edge in enumerate(self.final_edges):
            edge_id = f"edge_{i}"
            value = edge.get("label") if edge.get("label") else ""
            
            base_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
            edge_style = base_style + edge.get("style_attrs", "")
            
            cell = ET.SubElement(root, "mxCell", id=edge_id, value=value, style=edge_style, edge="1", parent="1", source=edge["from"], target=edge["to"])
            geom_edge = ET.SubElement(cell, "mxGeometry", relative="1")
            geom_edge.set("as", "geometry")
            
            # Добавляем waypoints (точки обхода), если они есть
            if edge.get("waypoints"):
                array_el = ET.SubElement(geom_edge, "Array")
                array_el.set("as", "points")
                for point in edge["waypoints"]:
                    ET.SubElement(array_el, "mxPoint", x=str(point["x"]), y=str(point["y"]))

        xml_str = ET.tostring(mxfile, encoding='utf-8')
        return minidom.parseString(xml_str).toprettyxml(indent="  ")

