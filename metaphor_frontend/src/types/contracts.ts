// 接口数据的公共类型
export type TaskStatus = "queued" | "running" | "succeeded" | "failed";

export type Idea = {
  id: string;
  title: string;
  tags?: string[];
  thumb?: string;
};

export type MappingChannel = {
  field: string;
  enc: "color" | "size" | "opacity" | "position";
  mark: "point" | "line" | "area" | "bar" | "arc";
  rationale?: string;
};

export type Mapping = { channels: MappingChannel[] };

export type Task = {
  status: TaskStatus;
  progress?: number;
  result?: {
    ideas?: Idea[];
    imageUrl?: string;
    mapping?: Mapping;
    [k: string]: unknown;
  };
  error?: string | null;
};
