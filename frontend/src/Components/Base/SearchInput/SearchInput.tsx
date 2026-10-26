// React
import type React from "react";

// Third Party
import { Search } from "lucide-react";
import { Form, InputGroup } from "react-bootstrap";

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}

/** Text field with a search icon, used above lists and tables. */
export const SearchInput: React.FC<SearchInputProps> = ({ value, onChange, placeholder }) => (
  <InputGroup className="aa-search-input">
    <InputGroup.Text className="bg-dark border-secondary text-secondary">
      <Search size={16} aria-hidden="true" />
    </InputGroup.Text>
    <Form.Control
      type="text"
      placeholder={placeholder}
      aria-label={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-dark text-light border-secondary"
    />
  </InputGroup>
);

export default SearchInput;
