import argparse
import yaml
from pathlib import Path
from pydantic import ValidationError

from scheme_generator.models import SchemeSchema
from scheme_generator.layout import LayoutEngine
from scheme_generator.render import DrawioRenderer

def main():
    parser = argparse.ArgumentParser(description="Generate Draw.io scheme from YAML spec")
    parser.add_argument("input", help="Path to input YAML file")
    parser.add_argument("-o", "--output", help="Path to output Draw.io file (default: output.drawio)", default="output.drawio")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file {args.input} does not exist.")
        return

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        # Валидация по схеме Pydantic
        schema = SchemeSchema(**data)
        
        # Вычисление координат (Layout)
        engine = LayoutEngine(schema.nodes, schema.edges)
        positions, final_edges = engine.calculate_positions()
        
        # Рендеринг XML (Draw.io)
        renderer = DrawioRenderer(schema, positions, final_edges)
        xml_content = renderer.render()
        
        # Сохранение результата
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(xml_content)
            
        print(f"[{schema.meta.get('name', 'Scheme')}] Successfully generated -> {args.output}")

    except yaml.YAMLError as e:
        print(f"Error parse YAML: {e}")
    except ValidationError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    main()
